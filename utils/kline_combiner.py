# utils/kline_combiner.py
import copy
from core.Chan_base import stCombineK


# 基础辅助函数（仅K线合并使用）
def greater_than_0(x):
    return x > 1e-5

def less_than_0(x):
    return x < -1e-5

def equ_than_0(x):
    return abs(x) <= 1e-5

def _handle_independent_k(combs, pCur, pLast, pPrev, b_up):
    """内部函数：处理独立K线（不对外暴露）"""
    pPrev = pCur
    pLast += 1
    combs[pLast] = copy.deepcopy(combs[pCur])
    combs[pLast].isUp = b_up
    return combs, pLast, pPrev

def _handle_contained_k(combs, pLast, low, high, index, pos_end, pPrev, kline_list):
    """内部函数：处理包含K线（不对外暴露）"""
    is_up_trend = combs[pLast].isUp
    extreme_kline = kline_list[index]
    new_kline = kline_list[pos_end]

    # 按趋势更新合并K线时间
    if is_up_trend:
        if greater_than_0(new_kline.high - extreme_kline.high) or (equ_than_0(new_kline.high - extreme_kline.high) and new_kline.time > extreme_kline.time):
            combs[pLast].data.time = new_kline.time
        else:
            combs[pLast].data.time = extreme_kline.time
    else:
        if less_than_0(new_kline.low - extreme_kline.low) or (equ_than_0(new_kline.low - extreme_kline.low) and new_kline.time > extreme_kline.time):
            combs[pLast].data.time = new_kline.time
        else:
            combs[pLast].data.time = extreme_kline.time

    # 更新合并K线高低点和位置
    combs[pLast].data.low = low
    combs[pLast].data.high = high
    combs[pLast].pos_end = pos_end
    combs[pLast].pos_extreme = index
    pPrev = pLast
    return combs, pPrev

def combine_kline(kline_list):
    """
    对外暴露的K线合并主函数：处理包含关系，输出合并后的stCombineK列表
    
    参数:
        kline_list: 原始KLine对象列表
    返回:
        list: 合并后的stCombineK对象列表
    """
    if len(kline_list) < 2:
        return [stCombineK(k, i, i, i, False, i) for i, k in enumerate(kline_list)]

    # 初始化合并容器
    combs = [stCombineK(k, i, i, i, False, i) for i, k in enumerate(kline_list)]
    size = len(combs)
    pBegin = 0
    pLast = pBegin
    pPrev = pBegin
    pCur = pBegin + 1
    pEnd = pBegin + size - 1

    # 处理前两根K线
    if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and greater_than_0(combs[pCur].data.low - combs[pPrev].data.low):
        combs, pLast, pPrev = _handle_independent_k(combs, pCur, pLast, pPrev, True)
    elif less_than_0(combs[pCur].data.high - combs[pPrev].data.high) and less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
        combs, pLast, pPrev = _handle_independent_k(combs, pCur, pLast, pPrev, False)
    else:
        if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) or less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            combs, pPrev = _handle_contained_k(combs, pLast, combs[pPrev].data.low, combs[pCur].data.high, combs[pCur].pos_begin, combs[pCur].pos_begin, pPrev, kline_list)
        else:
            combs, pPrev = _handle_contained_k(combs, pLast, combs[pCur].data.low, combs[pPrev].data.high, combs[pPrev].pos_begin, combs[pCur].pos_begin, pPrev, kline_list)
    pCur += 1

    # 处理后续K线
    while pCur <= pEnd:
        if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and greater_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            combs, pLast, pPrev = _handle_independent_k(combs, pCur, pLast, pPrev, True)
        elif less_than_0(combs[pCur].data.high - combs[pPrev].data.high) and less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            combs, pLast, pPrev = _handle_independent_k(combs, pCur, pLast, pPrev, False)
        else:
            if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) or less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
                if combs[pLast].isUp:
                    pos_index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].data.high - combs[pPrev].data.high) else combs[pCur].pos_begin
                    combs, pPrev = _handle_contained_k(combs, pLast, combs[pPrev].data.low, combs[pCur].data.high, pos_index, combs[pCur].pos_begin, pPrev, kline_list)
                else:
                    pos_index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].data.low - combs[pPrev].data.low) else combs[pCur].pos_begin
                    combs, pPrev = _handle_contained_k(combs, pLast, combs[pCur].data.low, combs[pPrev].data.high, pos_index, combs[pCur].pos_begin, pPrev, kline_list)
            else:
                if combs[pLast].isUp:
                    pos_index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end else combs[pPrev].pos_extreme
                    combs, pPrev = _handle_contained_k(combs, pLast, combs[pCur].data.low, combs[pPrev].data.high, pos_index, combs[pCur].pos_begin, pPrev, kline_list)
                else:
                    pos_index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end else combs[pPrev].pos_extreme
                    combs, pPrev = _handle_contained_k(combs, pLast, combs[pPrev].data.low, combs[pCur].data.high, pos_index, combs[pCur].pos_begin, pPrev, kline_list)
        pCur += 1
    
    # 按照新的排序对combs[:pLast + 1]的index属性进行重新赋值
    sorted_combs = sorted(combs[:pLast + 1], key=lambda x: x.data.time)
    for i, comb in enumerate(sorted_combs):
        comb.index = i

    return combs[:pLast + 1]
