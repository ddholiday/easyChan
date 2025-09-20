# utils/stroke_identifier.py
from datetime import datetime
from core.Chan_base import Stroke
from utils import (
    combine_kline,
    detect_fractals,
    find_all_necessary_points,
    print_necessary_points
)

from core.Chan_base import KLine


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

def identify_strokes_from_necessary_points(combined_klines, top_fractals, bottom_fractals, necessary_point_begin, necessary_point_end):
    """
    从给定的合并K线和分型中识别符合条件的笔序列
    
    参数:
        combined_klines: 合并后的K线列表(stCombineK对象)
        top_fractals: 顶分型列表
        bottom_fractals: 底分型列表
        necessary_point_begin: 起始必要分型（顶或底）
        necessary_point_end: 结束必要分型（与起始类型相反）
    
    返回:
        符合条件的笔序列（分型列表）
    """
    # 1. 筛选出在必要点之间的所有分型并按时间排序
    all_fractals = []
    
    # 确定时间范围
    start_time = min(necessary_point_begin.time, necessary_point_end.time)
    end_time = max(necessary_point_begin.time, necessary_point_end.time)
    
    # 筛选顶分型
    for tf in top_fractals:
        if start_time < tf.time < end_time:
            all_fractals.append(tf)
    
    # 筛选底分型
    for bf in bottom_fractals:
        if start_time < bf.time < end_time:
            all_fractals.append(bf)
    
    # 添加必要点并按时间排序
    all_fractals.append(necessary_point_begin)
    all_fractals.append(necessary_point_end)
    all_fractals.sort(key=lambda x: x.time)
    
    # 2. 动态规划准备工作
    n = len(all_fractals)
    if n < 2:
        return []  # 至少需要起点和终点两个分型
    
    # 查找起点和终点在列表中的索引
    try:
        start_idx = all_fractals.index(necessary_point_begin)
        end_idx = all_fractals.index(necessary_point_end)
    except ValueError:
        return []  # 理论上不会发生，因为我们刚刚添加了这两个点
    
    # 确保起点在终点之前
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx
    
    # 3. 检查两个分型之间是否符合笔的条件
    def is_valid_stroke(f1, f2):
        """检查两个分型之间是否能构成一笔"""
        # 条件1: 类型必须相反
        if f1.fractal_type == f2.fractal_type:
            return False
        
        # 条件2: 时间顺序必须正确
        if f1.time >= f2.time:
            return False
        
        # 条件3: 找到两个分型对应的K线索引
        # 注意：combined_klines中的是stCombineK对象，时间在其data属性中
        k1_idx = None
        k2_idx = None
        for i, combine_k in enumerate(combined_klines):
            # 访问stCombineK对象的时间需要通过data属性
            if combine_k.data.time == f1.time:
                k1_idx = i
            if combine_k.data.time == f2.time:
                k2_idx = i
            if k1_idx is not None and k2_idx is not None:
                break
        
        if k1_idx is None or k2_idx is None:
            return False  # 未找到对应的K线
        
        # 条件4: 非共用K线至少1根
        if abs(f1.combined_klines[1].index - f2.combined_klines[1].index) <= 3:
            return False
        
        # 条件5: 价格约束检查
        if f1.fractal_type == 'top':  # 顶->底，下降笔
            # 中间K线最高价不能超过顶分型价格
            for i in range(k1_idx + 1, k2_idx):
                if combined_klines[i].data.high > f1.price:
                    return False
        else:  # 底->顶，上升笔
            # 中间K线最低价不能低于底分型价格
            for i in range(k1_idx + 1, k2_idx):
                if combined_klines[i].data.low < f1.price:
                    return False
        
        return True
    
    # 4. 动态规划表初始化
    # dp[i] = (最长有效序列长度, 前一个分型的索引)
    dp = [(-1, -1) for _ in range(n)]
    dp[start_idx] = (1, -1)  # 起点序列长度为1，无前驱
    
    # 5. 填充动态规划表
    for i in range(start_idx + 1, end_idx + 1):
        for j in range(start_idx, i):
            # 检查j到i是否能构成一笔且类型相反
            if is_valid_stroke(all_fractals[j], all_fractals[i]):
                # 如果从j到i是有效的，且j有有效序列
                if dp[j][0] != -1 and dp[j][0] + 1 > dp[i][0]:
                    dp[i] = (dp[j][0] + 1, j)
    
    # 6. 回溯找到最长序列
    if dp[end_idx][0] == -1:
        return []  # 没有找到有效序列
    
    # 从终点回溯到起点
    stroke_sequence = []
    current_idx = end_idx
    
    while current_idx != -1:
        stroke_sequence.append(all_fractals[current_idx])
        current_idx = dp[current_idx][1]
    
    # 反转得到正确的顺序（从起点到终点）
    stroke_sequence.reverse()
    
    return stroke_sequence


def identify_strokes(combined_klines, necessary_points, top_fractals, bottom_fractals):
    """
    对外暴露的笔识别函数：基于必经点构建符合缠论规则的笔
    采用滑动窗口方式，对必经点两两一组处理
    
    参数:
        combined_klines: 合并后的stCombineK对象列表
        necessary_points: 必经点字典列表（find_all_necessary_points返回值）
        top_fractals: 顶分型列表
        bottom_fractals: 底分型列表
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
    
    # 2. 滑动窗口处理：两两一组处理必经点
    all_stroke_fractals = []
    # 从第0个点开始，每次取当前点和下一个点组成窗口
    for i in range(len(valid_points_sorted) - 1):
        current_point = valid_points_sorted[i]
        next_point = valid_points_sorted[i + 1]
        
        # 检查两个点类型是否相反
        if current_point["type"] == next_point["type"]:
            print(f"[笔识别] 警告：第{i}组必经点类型相同（{current_point['type']}），跳过处理")
            continue
        
        # 3. 调用辅助函数识别当前窗口内的笔序列
        window_fractals = identify_strokes_from_necessary_points(
            combined_klines=combined_klines,
            top_fractals=top_fractals,
            bottom_fractals=bottom_fractals,
            necessary_point_begin=current_point["fractal_obj"],
            necessary_point_end=next_point["fractal_obj"]
        )
        
        if not window_fractals or len(window_fractals) < 2:
            print(f"[笔识别] 第{i}组必经点之间未识别到有效笔序列")
            continue
        
        # 避免重复添加（当前窗口的终点是下一个窗口的起点）
        if i > 0 and all_stroke_fractals and all_stroke_fractals[-1] == window_fractals[0]:
            all_stroke_fractals.extend(window_fractals[1:])
        else:
            all_stroke_fractals.extend(window_fractals)
    
    # 去重处理（确保分型序列连续且不重复）
    unique_fractals = []
    seen = set()
    for fractal in all_stroke_fractals:
        if fractal.time not in seen:
            seen.add(fractal.time)
            unique_fractals.append(fractal)
    all_stroke_fractals = unique_fractals
    
    if not all_stroke_fractals or len(all_stroke_fractals) < 2:
        print("[笔识别] 整体未识别到有效的笔序列")
        return []
    
    # 4. 将分型序列转换为Stroke对象列表
    stroke_list = []
    for i in range(len(all_stroke_fractals) - 1):
        start_fractal = all_stroke_fractals[i]
        end_fractal = all_stroke_fractals[i + 1]
        
        # 确定笔的方向
        if start_fractal.fractal_type == "bottom" and end_fractal.fractal_type == "top":
            direction = "up"
        else:
            direction = "down"
        
        # 创建Stroke对象
        stroke = Stroke(
            start_fractal=start_fractal,
            end_fractal=end_fractal,
        )
        stroke_list.append(stroke)
    
    print(f"[笔识别] 成功识别 {len(stroke_list)} 笔")
    return stroke_list

def identify_strokes_from_pandas(df):
    """
    从Pandas DataFrame中识别笔
    """
    def df_to_kline_list(df):
        """将DataFrame转换为KLine对象列表（核心数据格式转换）"""
        # 重置索引
        df = df.reset_index(drop=True)
        kline_list = []
        for index, row in df.iterrows():
            kline = KLine(
                time=row['date'].timestamp(),  # 时间戳（便于后续计算）
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                symbol="HS300",  # 标的名称（可根据数据修改）
                index=index
            )
            kline_list.append(kline)
        print(f"✅ 转换为{len(kline_list)}个KLine对象")
        return kline_list
    # 转换为KLine对象列表
    kline_list = df_to_kline_list(df)

    # 合并K线（根据实际情况调整参数）
    combined_klines = combine_kline(kline_list)
    
    # 检测分型
    top_fractals, bottom_fractals = detect_fractals(combined_klines)
    
    # 查找必经点
    necessary_points = find_all_necessary_points(combined_klines, top_fractals, bottom_fractals)
    
    # 识别笔
    stroke_list = identify_strokes(combined_klines, necessary_points, top_fractals, bottom_fractals)
    
    return stroke_list, kline_list, combined_klines, top_fractals, bottom_fractals

def identify_strokes_from_klines(kline_list):
    """
    从KLine对象列表中识别笔
    """
    # 合并K线（根据实际情况调整参数）
    combined_klines = combine_kline(kline_list)
    
    # 检测分型
    top_fractals, bottom_fractals = detect_fractals(combined_klines)
    
    # 查找必经点
    necessary_points = find_all_necessary_points(combined_klines, top_fractals, bottom_fractals)
    
    # 识别笔
    stroke_list = identify_strokes(combined_klines, necessary_points, top_fractals, bottom_fractals)
    
    return stroke_list, combined_klines, top_fractals, bottom_fractals