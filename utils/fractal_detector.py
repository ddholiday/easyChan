# utils/fractal_detector.py
from core.Chan_base import TopFractal, BottomFractal


# 复用K线合并中的辅助函数（避免重复定义，直接导入或重新定义）
def greater_than_0(x):
    return x > 1e-5

def less_than_0(x):
    return x < -1e-5

def detect_fractals(combined_klines):
    """
    对外暴露的分型检测函数：从合并后的K线中识别顶分型和底分型
    
    参数:
        combined_klines: 合并后的stCombineK对象列表
    返回:
        tuple: (top_fractals列表, bottom_fractals列表)
    """
    top_fractals = []
    bottom_fractals = []

    # 遍历合并K线（需至少3根K线构成分型）
    for i in range(1, len(combined_klines) - 1):
        k0 = combined_klines[i-1].data  # 左侧K线
        k1 = combined_klines[i].data    # 中间K线（分型核心）
        k2 = combined_klines[i+1].data  # 右侧K线

        # 检测顶分型（中间K线最高价 > 两侧，且最低价 > 两侧，增强严格性）
        if (greater_than_0(k1.high - k0.high) and greater_than_0(k1.high - k2.high) and
            greater_than_0(k1.low - k0.low) and greater_than_0(k1.low - k2.low)):
            try:
                top_fractals.append(TopFractal([k0, k1, k2]))
            except ValueError:
                continue  # 过滤不符合严格条件的分型

        # 检测底分型（中间K线最低价 < 两侧，且最高价 < 两侧，增强严格性）
        if (less_than_0(k1.low - k0.low) and less_than_0(k1.low - k2.low) and
            less_than_0(k1.high - k0.high) and less_than_0(k1.high - k2.high)):
            try:
                bottom_fractals.append(BottomFractal([k0, k1, k2]))
            except ValueError:
                continue  # 过滤不符合严格条件的分型

    print(f"[分型检测] 共识别到 {len(top_fractals)} 个顶分型，{len(bottom_fractals)} 个底分型")
    return top_fractals, bottom_fractals