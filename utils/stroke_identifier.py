# utils/stroke_identifier.py
from datetime import datetime
from core.Chan_base import Stroke


def _validate_stroke_conditions(start_point, end_point, combined_klines, last_direction):
    """
    内部函数：验证笔的核心条件（类型相反、时间顺序、价格范围等）
    
    参数:
        start_point: 起点必经点字典（含time/type/fractal_obj）
        end_point: 终点必经点字典（含time/type/fractal_obj）
        combined_klines: 合并后的stCombineK对象列表
        last_direction: 上一笔方向（up/down，用于验证交替性）
    返回:
        tuple: (is_valid, direction, start_idx, end_idx, bottom_fractal, top_fractal)
        - is_valid: 是否符合笔条件（bool）
        - direction: 笔方向（up/down，仅is_valid=True时有效）
        - start_idx/end_idx: 起点/终点在合并K线中的索引（仅is_valid=True时有效）
        - bottom_fractal/top_fractal: 笔的底/顶分型（仅is_valid=True时有效）
    """
    # 条件1：起点和终点类型必须相反
    if start_point["type"] == end_point["type"]:
        return False, None, None, None, None, None

    # 条件2：确定笔方向和顶底分型
    if start_point["type"] == "bottom" and end_point["type"] == "top":
        direction = "up"
        bottom_fractal = start_point["fractal_obj"]
        top_fractal = end_point["fractal_obj"]
    else:
        direction = "down"
        bottom_fractal = end_point["fractal_obj"]
        top_fractal = start_point["fractal_obj"]

    # 条件3：与上一笔方向必须交替（上一笔存在时）
    if last_direction is not None and direction == last_direction:
        return False, None, None, None, None, None

    # 条件4：获取分型在合并K线中的索引（验证时间顺序）
    combined_times = [k.data.time for k in combined_klines]
    try:
        start_idx = combined_times.index(start_point["time"])
        end_idx = combined_times.index(end_point["time"])
    except ValueError:
        return False, None, None, None, None, None  # 分型不在合并K线中

    # 条件5：时间顺序正确（起点在前，终点在后）
    if start_idx >= end_idx:
        return False, None, None, None, None, None

    # 条件6：非共用K线数量足够（至少1根）
    if (end_idx - start_idx - 1) < 1:
        return False, None, None, None, None, None

    # 条件7：中间K线价格不超出顶底分型范围
    middle_klines = combined_klines[start_idx + 1: end_idx]
    middle_high = max(k.data.high for k in middle_klines)
    middle_low = min(k.data.low for k in middle_klines)
    if middle_high > top_fractal.price or middle_low < bottom_fractal.price:
        return False, None, None, None, None, None

    # 所有条件满足
    return True, direction, start_idx, end_idx, bottom_fractal, top_fractal


def identify_strokes(combined_klines, necessary_points):
    """
    对外暴露的笔识别函数：基于必经点构建符合缠论规则的笔
    
    参数:
        combined_klines: 合并后的stCombineK对象列表
        necessary_points: 必经点字典列表（find_all_necessary_points返回值）
    返回:
        list: 识别到的笔列表（Stroke对象）
    """
    if len(necessary_points) < 2:
        print("[笔识别] 警告：有效必经点不足2个，无法构建笔")
        return []

    # 1. 预处理必经点：提取核心信息并按时间排序
    valid_points = []
    for point in necessary_points:
        fractal = point.get("fractal")
        if not fractal:
            continue
        valid_points.append({
            "time": fractal.time,
            "type": point["top_or_bottom"],  # top/bottom
            "fractal_obj": fractal
        })
    # 按时间排序（确保笔的时间顺序正确）
    valid_points_sorted = sorted(valid_points, key=lambda x: x["time"])
    print(f"[笔识别] 预处理后有效必经点数量：{len(valid_points_sorted)}（已按时间排序）")

    # 2. 构建笔序列（核心逻辑：保证交替性和首尾衔接）
    strokes = []
    last_end_fractal = None  # 上一笔的结束分型（用于衔接）
    last_direction = None    # 上一笔的方向（用于交替验证）
    current_start_idx = 0    # 当前起点在必经点列表中的索引

    while current_start_idx < len(valid_points_sorted) - 1:
        # 衔接上一笔的结束点：找到与上一笔结束分型一致的必经点
        if last_end_fractal is not None:
            found衔接 = False
            for i in range(current_start_idx, len(valid_points_sorted)):
                if valid_points_sorted[i]["fractal_obj"] == last_end_fractal:
                    current_start_idx = i
                    found衔接 = True
                    break
            if not found衔接:
                print("[笔识别] 警告：无法衔接上一笔，终止笔构建")
                break

        # 当前起点
        start_point = valid_points_sorted[current_start_idx]
        found_valid_end = False  # 是否找到有效终点

        # 遍历后续必经点，寻找有效终点
        for end_idx in range(current_start_idx + 1, len(valid_points_sorted)):
            end_point = valid_points_sorted[end_idx]

            # 验证笔的核心条件
            is_valid, direction, k_start_idx, k_end_idx, bottom_f, top_f = _validate_stroke_conditions(
                start_point, end_point, combined_klines, last_direction
            )
            if not is_valid:
                continue

            # 条件满足：构建笔对象
            # 笔包含的K线：从起点分型到终点分型的合并K线
            stroke_klines = [k.data for k in combined_klines[k_start_idx: k_end_idx + 1]]
            new_stroke = Stroke(
                start_fractal=start_point["fractal_obj"],
                end_fractal=end_point["fractal_obj"],
                klines=stroke_klines,
                direction=direction
            )
            new_stroke.confirm()  # 标记为已确认的笔
            strokes.append(new_stroke)

            # 更新状态：用于下一笔的衔接和交替
            last_end_fractal = end_point["fractal_obj"]
            last_direction = direction
            current_start_idx = end_idx  # 下一笔起点设为当前终点
            found_valid_end = True
            break

        # 未找到有效终点：尝试下一个起点
        if not found_valid_end:
            current_start_idx += 1

    # 打印笔识别结果
    print(f"[笔识别] 最终构建笔数量：{len(strokes)}")
    for i, stroke in enumerate(strokes, 1):
        start_time = datetime.fromtimestamp(stroke.start_fractal.time).strftime("%Y-%m-%d")
        end_time = datetime.fromtimestamp(stroke.end_fractal.time).strftime("%Y-%m-%d")
        print(f"  笔{i}：{stroke.direction.upper()}（{start_time} ~ {end_time}），振幅：{stroke.amplitude:.2f}")

    return strokes