# utils/__init__.py
# 从各细分文件导入核心函数，对外提供统一接口（避免用户关心内部拆分）
from .kline_combiner import combine_kline
from .fractal_detector import detect_fractals
from .necessary_point_finder import find_all_necessary_points, print_necessary_points
from .stroke_identifier import identify_strokes, identify_strokes_from_necessary_points, identify_strokes_from_pandas, identify_strokes_from_klines

# 定义__all__：明确对外暴露的函数列表（规范导入）
__all__ = [
    "combine_kline",          # K线合并
    "detect_fractals",        # 分型检测
    "find_all_necessary_points",  # 必经点查找
    "print_necessary_points", # 必经点打印（辅助）
    "identify_strokes",        # 笔识别
    "identify_strokes_from_necessary_points"  # 基于必经点的笔识别
    "identify_strokes_from_pandas",
    "identify_strokes_from_klines"
]