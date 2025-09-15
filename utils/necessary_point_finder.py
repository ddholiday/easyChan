# utils/necessary_point_finder.py
from datetime import datetime


def _find_initial_points(combined_klines, top_fractals, bottom_fractals):
    """内部函数：寻找全局初始必经点（最高顶+最低底）"""
    if not top_fractals or not bottom_fractals:
        print("[必经点查找] 警告：顶分型或底分型列表为空")
        return None

    # 筛选全局极值
    potential_top = max(top_fractals, key=lambda x: x.price)
    potential_bottom = min(bottom_fractals, key=lambda x: x.price)

    # 验证分型在合并K线中存在
    combined_times = [k.data.time for k in combined_klines]
    try:
        top_idx = combined_times.index(potential_top.time)
        bottom_idx = combined_times.index(potential_bottom.time)
    except ValueError:
        print("[必经点查找] 警告：分型未在合并K线中找到对应记录")
        return None

    # 验证分型间非共用K线
    if abs(potential_top.klines[1].index - potential_bottom.klines[1].index) > 3:
        return {"top_necessary": potential_top, "bottom_necessary": potential_bottom}
    else:
        print(f"[必经点查找] 警告：顶底分型间距不足（索引差={abs(top_idx - bottom_idx)}）")
        return None

def _recursive_front(segment, top_fractals, bottom_fractals, result_list, is_split_by_top):
    """内部函数：前段递归查找必经点"""
    if len(segment) < 3:
        return

    if is_split_by_top:
        # 被顶分型分割：找段内最低底分型
        if not bottom_fractals:
            return
        potential_bottom = min(bottom_fractals, key=lambda x: x.price)
        segment_times = [k.data.time for k in segment]

        try:
            bottom_idx = segment_times.index(potential_bottom.time)
        except ValueError:
            return

        if bottom_idx < len(segment) - 1:
            result_list.append({
                "type": "recursive",
                "top_or_bottom": "bottom",
                "fractal": potential_bottom,
                "segment_type": "front"
            })
            # 分割新前段继续递归
            new_front = segment[:bottom_idx]
            new_tops = [f for f in top_fractals if f.time in [k.data.time for k in new_front]]
            new_bottoms = [f for f in bottom_fractals if f.time in [k.data.time for k in new_front]]
            _recursive_front(new_front, new_tops, new_bottoms, result_list, False)
    else:
        # 被底分型分割：找段内最高顶分型
        if not top_fractals:
            return
        potential_top = max(top_fractals, key=lambda x: x.price)
        segment_times = [k.data.time for k in segment]

        try:
            top_idx = segment_times.index(potential_top.time)
        except ValueError:
            return

        if top_idx < len(segment) - 1:
            result_list.append({
                "type": "recursive",
                "top_or_bottom": "top",
                "fractal": potential_top,
                "segment_type": "front"
            })
            # 分割新前段继续递归
            new_front = segment[:top_idx]
            new_tops = [f for f in top_fractals if f.time in [k.data.time for k in new_front]]
            new_bottoms = [f for f in bottom_fractals if f.time in [k.data.time for k in new_front]]
            _recursive_front(new_front, new_tops, new_bottoms, result_list, True)

def _recursive_back(segment, top_fractals, bottom_fractals, result_list, is_start_with_top):
    """内部函数：后段递归查找必经点"""
    if len(segment) < 3:
        return

    if is_start_with_top:
        # 起始为顶分型：找段内最低底分型
        if not bottom_fractals:
            return
        potential_bottom = min(bottom_fractals, key=lambda x: (x.price, -x.time))
        segment_times = [k.data.time for k in segment]

        try:
            bottom_idx = segment_times.index(potential_bottom.time)
        except ValueError:
            return

        if bottom_idx > 0:
            result_list.append({
                "type": "recursive",
                "top_or_bottom": "bottom",
                "fractal": potential_bottom,
                "segment_type": "back"
            })
            # 分割新后段继续递归
            new_back = segment[bottom_idx + 1:]
            new_tops = [f for f in top_fractals if f.time in [k.data.time for k in new_back]]
            new_bottoms = [f for f in bottom_fractals if f.time in [k.data.time for k in new_back]]
            _recursive_back(new_back, new_tops, new_bottoms, result_list, False)
    else:
        # 起始为底分型：找段内最高顶分型
        if not top_fractals:
            return
        potential_top = max(top_fractals, key=lambda x: x.price)
        segment_times = [k.data.time for k in segment]

        try:
            top_idx = segment_times.index(potential_top.time)
        except ValueError:
            return

        if top_idx > 0:
            result_list.append({
                "type": "recursive",
                "top_or_bottom": "top",
                "fractal": potential_top,
                "segment_type": "back"
            })
            # 分割新后段继续递归
            new_back = segment[top_idx + 1:]
            new_tops = [f for f in top_fractals if f.time in [k.data.time for k in new_back]]
            new_bottoms = [f for f in bottom_fractals if f.time in [k.data.time for k in new_back]]
            _recursive_back(new_back, new_tops, new_bottoms, result_list, True)

def find_all_necessary_points(combined_klines, top_fractals, bottom_fractals):
    """
    对外暴露的必经点查找入口：整合初始查找与递归查找
    
    参数:
        combined_klines: 合并后的stCombineK对象列表
        top_fractals: 顶分型列表（TopFractal对象）
        bottom_fractals: 底分型列表（BottomFractal对象）
    返回:
        list: 所有必经点字典列表（含初始/递归类型、分型信息）
    """
    all_points = []
    # 1. 查找初始必经点
    initial_points = _find_initial_points(combined_klines, top_fractals, bottom_fractals)
    if not initial_points:
        return all_points

    # 添加初始必经点到结果
    all_points.append({
        "type": "initial",
        "top_or_bottom": "top",
        "fractal": initial_points["top_necessary"],
        "segment_type": "full"
    })
    all_points.append({
        "type": "initial",
        "top_or_bottom": "bottom",
        "fractal": initial_points["bottom_necessary"],
        "segment_type": "full"
    })

    # 2. 确定初始必经点在合并K线中的索引
    combined_times = [k.data.time for k in combined_klines]
    try:
        top_idx = combined_times.index(initial_points["top_necessary"].time)
        bottom_idx = combined_times.index(initial_points["bottom_necessary"].time)
    except ValueError:
        print("[必经点查找] 警告：初始必经点在合并K线中未找到对应索引")
        return all_points

    # 3. 分割前段和后段，执行递归查找
    start_idx = min(top_idx, bottom_idx)
    end_idx = max(top_idx, bottom_idx)

    # 前段递归（起点→start_idx）
    front_segment = combined_klines[:start_idx]
    front_tops = [f for f in top_fractals if f.time in [k.data.time for k in front_segment]]
    front_bottoms = [f for f in bottom_fractals if f.time in [k.data.time for k in front_segment]]
    _recursive_front(front_segment, front_tops, front_bottoms, all_points, top_idx < bottom_idx)

    # 后段递归（end_idx→终点）
    back_segment = combined_klines[end_idx:]
    back_tops = [f for f in top_fractals if f.time in [k.data.time for k in back_segment]]
    back_bottoms = [f for f in bottom_fractals if f.time in [k.data.time for k in back_segment]]
    _recursive_back(back_segment, back_tops, back_bottoms, all_points, top_idx > bottom_idx)

    # 打印必经点统计信息
    initial_count = len([p for p in all_points if p["type"] == "initial"])
    recursive_count = len([p for p in all_points if p["type"] == "recursive"])
    print(f"[必经点查找] 共找到 {len(all_points)} 个必经点（初始：{initial_count} 个，递归：{recursive_count} 个）")
    return all_points


def print_necessary_points(points):
    """
    辅助函数：格式化打印必经点信息（便于调试）
    
    参数:
        points: 必经点字典列表（find_all_necessary_points返回值）
    """
    if not points:
        print("[必经点打印] 未找到任何必经点")
        return
    print("\n" + "="*30 + " 必经点详情 " + "="*30)
    for i, point in enumerate(points, 1):
        fractal = point["fractal"]
        time_str = datetime.fromtimestamp(fractal.time).strftime("%Y-%m-%d %H:%M:%S")
        print(f"第{i}个必经点：")
        print(f"  - 类型：{'初始必经点' if point['type'] == 'initial' else '递归必经点'}")
        print(f"  - 分型：{'顶分型' if point['top_or_bottom'] == 'top' else '底分型'}")
        print(f"  - 时间：{time_str}")
        print(f"  - 价格：{fractal.price:.2f}")
        print(f"  - 分段：{point['segment_type']}")
    print("="*68)

