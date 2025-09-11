import copy
from datetime import datetime


class KLine:
    """基础K线类：存储单根K线的时间、价格、成交量信息"""
    def __init__(self, time=0, open=0, high=0, low=0, close=0, volume=0, symbol=""):
        self.time = time          # 时间戳（方便后续转换）
        self.open = open          # 开盘价
        self.high = high          # 最高价
        self.low = low            # 最低价
        self.close = close        # 收盘价
        self.volume = volume      # 成交量
        self.symbol = symbol      # 标的代码（如HS300）

    def __repr__(self):
        time_str = datetime.fromtimestamp(self.time).strftime("%Y-%m-%d")
        return f"KLine(time={time_str}, open={self.open:.2f}, high={self.high:.2f}, low={self.low:.2f}, close={self.close:.2f})"


class stCombineK:
    """K线合并容器类：存储合并后的K线及位置信息"""
    def __init__(self, data, begin, end, base, isup):
        self.data = data          # KLine对象（合并后的K线数据）
        self.pos_begin = begin    # 合并起始位置索引（原始K线）
        self.pos_end = end        # 合并结束位置索引（原始K线）
        self.pos_extreme = base   # 极值位置索引（高点/低点对应的原始K线）
        self.isUp = isup          # 趋势方向：True=向上，False=向下


class Fractal:
    """分型基类：顶分型和底分型的父类，定义公共属性和接口"""
    def __init__(self, klines):
        if len(klines) < 3:
            raise ValueError("分型需至少3根K线")
        self.klines = klines          # 构成分型的3根KLine对象列表
        self.is_confirmed = False     # 是否被后续K线确认（外部逻辑更新）

    @property
    def time(self):
        return self.klines[1].time    # 分型时间取中间K线时间

    @property
    def fractal_type(self):
        raise NotImplementedError("子类必须实现fractal_type属性")

    def __repr__(self):
        time_str = datetime.fromtimestamp(self.time).strftime("%Y-%m-%d")
        return f"{self.fractal_type.capitalize()}Fractal(time={time_str}, price={self.price:.2f}, confirmed={self.is_confirmed})"


class TopFractal(Fractal):
    """顶分型：中间K线最高价 > 左右两侧K线最高价"""
    def __init__(self, klines):
        super().__init__(klines)
        if not (klines[1].high > klines[0].high and klines[1].high > klines[2].high):
            raise ValueError("不符合顶分型条件：中间K线最高价需大于两侧")

    @property
    def price(self):
        return self.klines[1].high    # 顶分型价格=中间K线最高价

    @property
    def fractal_type(self):
        return 'top'


class BottomFractal(Fractal):
    """底分型：中间K线最低价 < 左右两侧K线最低价"""
    def __init__(self, klines):
        super().__init__(klines)
        if not (klines[1].low < klines[0].low and klines[1].low < klines[2].low):
            raise ValueError("不符合底分型条件：中间K线最低价需小于两侧")

    @property
    def price(self):
        return self.klines[1].low     # 底分型价格=中间K线最低价

    @property
    def fractal_type(self):
        return 'bottom'


class Stroke:
    """缠论笔类：由相邻且独立的顶分型和底分型构成"""
    def __init__(self, start_fractal, end_fractal, klines):
        # 验证1：分型类型必须相反（顶-底或底-顶）
        if start_fractal.fractal_type == end_fractal.fractal_type:
            raise ValueError("笔的起始和结束分型类型必须相反")
        
        # 验证2：分型间无共用K线
        start_k_times = [k.time for k in start_fractal.klines]
        end_k_times = [k.time for k in end_fractal.klines]
        if any(k_time in end_k_times for k_time in start_k_times):
            raise ValueError("分型间存在共用K线，不符合笔的定义")
        
        # 验证3：分型间至少1根独立K线
        if len(klines) - len(start_fractal.klines) - len(end_fractal.klines) < 1:
            raise ValueError("分型间至少需1根独立K线")

        # 基础属性赋值
        self.start_fractal = start_fractal  # 起始分型
        self.end_fractal = end_fractal      # 结束分型
        self.klines = klines                # 笔包含的所有K线
        self.direction = 'up' if isinstance(start_fractal, BottomFractal) else 'down'
        self.is_confirmed = False           # 是否被确认（外部逻辑更新）
        self.high = max(k.high for k in self.klines)  # 笔的最高价
        self.low = min(k.low for k in self.klines)    # 笔的最低价

    def confirm(self):
        """标记笔被后续K线确认（如出现反向分型）"""
        self.is_confirmed = True

    @property
    def amplitude(self):
        """笔的振幅（价格波动范围）"""
        return self.high - self.low

    @property
    def fractal_distance(self):
        """分型间K线数量"""
        return len(self.klines)

    def __repr__(self):
        status = "Confirmed" if self.is_confirmed else "Unconfirmed"
        start_time = datetime.fromtimestamp(self.start_fractal.time).strftime("%Y-%m-%d")
        end_time = datetime.fromtimestamp(self.end_fractal.time).strftime("%Y-%m-%d")
        return f"<{status} {self.direction.upper()} Stroke | {start_time}~{end_time} | K线数={self.fractal_distance} | 振幅={self.amplitude:.2f}>"