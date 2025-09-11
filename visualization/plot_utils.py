# visualization/plot_utils.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from core.Chan_base import Stroke


def plot_kline(ax, klines, title):
    """绘制K线图（蜡烛图）"""
    # 转换为matplotlib candlestick_ohlc所需格式：(matplotlib时间, open, high, low, close)
    quotes = [
        (
            mdates.date2num(datetime.fromtimestamp(k.time)),  # 时间戳→matplotlib日期
            k.open,
            k.high,
            k.low,
            k.close
        )
        for k in klines
    ]

    # 绘制蜡烛图
    from mpl_finance import candlestick_ohlc  # 局部导入（避免全局依赖冲突）
    candlestick_ohlc(
        ax, quotes,
        width=0.6,        # K线宽度（适配周线数据）
        colorup='red',    # 阳线颜色（收盘>开盘）
        colordown='green',# 阴线颜色（收盘<开盘）
        alpha=0.8         # 透明度（避免遮挡标记）
    )

    # 美化坐标轴
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # 日期格式
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # 每2个月显示1个刻度
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)  # 日期标签旋转45°，避免重叠
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)  # 标题样式
    ax.set_ylabel('价格', fontsize=10)  # Y轴标签
    ax.grid(True, linestyle='--', alpha=0.5)  # 网格线（辅助阅读）
    ax.spines['top'].set_visible(False)  # 隐藏上边框
    ax.spines['right'].set_visible(False)  # 隐藏右边框


def mark_fractals(ax, top_fractals, bottom_fractals):
    """在K线图上标记顶分型和底分型（含图例）"""
    # 标记顶分型：红色倒三角形（▽），位置在分型最高价
    if top_fractals:
        for i, top in enumerate(top_fractals):
            x = mdates.date2num(datetime.fromtimestamp(top.time))
            y = top.price
            # 绘制标记（仅第一个顶分型显示图例）
            label = '顶分型' if i == 0 else ""
            ax.scatter(
                x, y,
                marker='v',        # 倒三角形（顶分型向下指向高点）
                color='darkred',   # 深色更醒目，避免与阳线混淆
                s=100,             # 标记大小
                zorder=5,          # 图层优先级（高于K线，低于笔标注）
                label=label
            )

    # 标记底分型：绿色正三角形（△），位置在分型最低价
    if bottom_fractals:
        for i, bottom in enumerate(bottom_fractals):
            x = mdates.date2num(datetime.fromtimestamp(bottom.time))
            y = bottom.price
            # 绘制标记（仅第一个底分型显示图例）
            label = '底分型' if i == 0 else ""
            ax.scatter(
                x, y,
                marker='^',        # 正三角形（底分型向上指向低点）
                color='darkgreen', # 深色更醒目，避免与阴线混淆
                s=100,             # 标记大小
                zorder=5,          # 图层优先级
                label=label
            )

    # 添加图例（避免重复，固定在右上角）
    if top_fractals or bottom_fractals:
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)


def draw_strokes(ax, strokes):
    """在K线图上绘制笔（含连线和标注）"""
    if not strokes:
        return

    # 遍历每一笔，绘制连线+标注
    for i, stroke in enumerate(strokes):
        # 1. 获取笔的起始/结束信息
        start_f = stroke.start_fractal
        end_f = stroke.end_fractal
        # 转换时间格式（时间戳→matplotlib日期）
        start_x = mdates.date2num(datetime.fromtimestamp(start_f.time))
        end_x = mdates.date2num(datetime.fromtimestamp(end_f.time))
        # 分型价格（笔的起始/结束点）
        start_y = start_f.price
        end_y = end_f.price

        # 2. 笔的线条样式（按方向区分）
        if stroke.direction == 'up':  # 上升笔（底→顶）
            color = 'darkred'
            line_style = '-'  # 实线
        else:  # 下降笔（顶→底）
            color = 'darkgreen'
            line_style = '-'

        # 3. 绘制笔的连线（连接两个分型）
        ax.plot(
            [start_x, end_x],    # X轴：时间范围
            [start_y, end_y],    # Y轴：价格范围
            color=color,
            linestyle=line_style,
            linewidth=2,         # 线条宽度（突出笔结构）
            alpha=0.8,           # 透明度（避免遮挡K线）
            zorder=4,            # 图层优先级（低于分型标记，高于K线）
            # 仅第一个同方向笔显示图例
            label='上升笔' if (i == 0 and stroke.direction == 'up') else
                  ('下降笔' if (i == 0 and stroke.direction == 'down') else "")
        )

        # 4. 绘制笔的标注（显示序号+振幅，避免重叠）
        # 标注位置：笔的中间点，Y轴偏移振幅的5%（避免遮挡线条）
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2

    # 添加笔的图例（若有笔则显示）
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)


def create_kline_figure(figsize=(14, 10)):
    """创建双轴K线图（原始K线+合并后K线，共享X轴）"""
    # 创建2行1列的子图，共享X轴（避免重复显示日期）
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True, gridspec_kw={'height_ratios': [1, 1]})
    # 调整子图间距（避免标题与下轴重叠）
    plt.subplots_adjust(hspace=0.15)
    return fig, ax1, ax2