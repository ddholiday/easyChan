import pandas as pd
from utils import (
    identify_strokes_from_klines,
    combine_kline,
    detect_fractals
)
from visualization.plot_utils import (
    create_kline_figure,
    plot_kline,
    mark_fractals,
    draw_strokes,
    draw_buy_points
)
import matplotlib.pyplot as plt

from core.Chan_base import KLine

def greater_than_0(x):
    return x > 1e-5

def less_than_0(x):
    return x < -1e-5

def load_data(file_path):
    """读取CSV格式的K线数据，返回DataFrame"""
    try:
        df = pd.read_csv(file_path)
        # 保留最后N条数据（避免数据量过大）
        # 转换日期格式（确保后续能转时间戳）
        df['date'] = pd.to_datetime(df['date'])
        print(f"✅ 成功读取数据：{len(df)}条记录，时间范围：{df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
        return df
    except Exception as e:
        print(f"❌ 数据读取失败：{str(e)}")
        print("请检查文件路径是否正确，或CSV格式是否包含'date,open,high,low,close,volume'列")
        raise

DATA_PATH = "data/hs300_k_data_week.csv"  # 数据文件路径（根据实际情况修改）
df = load_data(DATA_PATH)

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
# 补充后续代码，实现买卖点检测逻辑
# 存储检测到的买卖点
buy_points = []
sell_points = []

for window_end in range(10, len(kline_list)):
    window = kline_list[0:window_end]
    if len(window) < 10:  # 确保窗口有足够数据
        continue
        
    # 合并K线并检测分型
    combined_kline = combine_kline(window)
    top_fractals, bottom_fractals = detect_fractals(combined_kline)
    
    # 确保有足够的合并K线来判断最后三根
    if len(combined_kline) < 3:
        continue

    last_combined_kline_index = combined_kline[-1]

    print("最后一根合并K线索引:", combined_kline[-1].index)

    last_top_fractal = top_fractals[-1] if top_fractals else None
    last_bottom_fractal = bottom_fractals[-1] if bottom_fractals else None

    print("最后一个顶分型索引:", last_top_fractal.end_index if last_top_fractal else "无")
    print("最后一个底分型索引:", last_bottom_fractal.end_index if last_bottom_fractal else "无")
    
    # 如果不是任何一种分型，跳过
    if not (last_top_fractal or last_bottom_fractal):
        continue

    # 如果最后一根合并K线不是最后一个分型，跳过
    if last_combined_kline_index.index != combined_kline[-1].index:
        continue

    # 识别笔
    strokes, _, _, _ = identify_strokes_from_klines(window)

    # 小于4笔，跳过
    if len(strokes) < 4:
        continue

    # 如果最后一笔的终点不是最后一个分型，跳过
    print("最后一笔的终点索引:", strokes[-1].end_point.index)
    print("最后一个分型索引:", combined_kline[-1].index)

    if strokes[-1].end_point.index != combined_kline[-1].index:
        continue

    is_bottom_fractal = last_bottom_fractal and last_combined_kline_index.index == last_bottom_fractal.end_index
    is_top_fractal = last_top_fractal and last_combined_kline_index.index == last_top_fractal.end_index
    
    # 判断是否为二买点（条件2）
    is_second_buy = False
    if is_bottom_fractal and len(strokes) >= 4:
        # 二买点条件：前一笔是向下的笔，且底分型低于前一个向上笔的终点
        # 这里简化处理，实际需根据笔的方向和高低点判断
        last_four_strokes = strokes[-4:]
        # 打印最后4笔的方向
        print("最后4笔的方向:", [stroke.direction for stroke in last_four_strokes])

        if (last_four_strokes[0].direction == 'up' and 
            last_four_strokes[1].direction == 'down' and
            last_four_strokes[2].direction == 'up' and
            last_four_strokes[3].direction == 'down' and
            last_four_strokes[0].start_fractal.low >= last_four_strokes[2].start_fractal.low and
            last_four_strokes[3].end_fractal.low >= last_four_strokes[2].start_fractal.low):
            is_second_buy = True
    
    # 判断是否为二卖点（条件2）
    is_second_sell = False
    if is_top_fractal and len(strokes) >= 4:
        # 二卖点条件：前一笔是向上的笔，且顶分型高于前一个向下笔的终点
        last_four_strokes = strokes[-4:]
        if (last_four_strokes[0].direction == 'down' and 
            last_four_strokes[1].direction == 'up' and
            last_four_strokes[2].direction == 'down' and
            last_four_strokes[3].direction == 'up' and
            last_four_strokes[0].start_fractal.high <= last_four_strokes[2].start_fractal.high and
            last_four_strokes[3].end_fractal.high <= last_four_strokes[2].start_fractal.high):
            is_second_sell = True
    
    # 记录买卖点
    current_kline = window[-1]
    if is_bottom_fractal and is_second_buy:
        buy_points.append({
            'time': current_kline.time,
            'price': current_kline.close,
            'index': window_end
        })
        print(f"📈 检测到二买点：时间={pd.to_datetime(current_kline.time)}, 价格={current_kline.close}")
    
    if is_top_fractal and is_second_sell:
        sell_points.append({
            'time': current_kline.time,
            'price': current_kline.close,
            'index': window_end
        })
        print(f"📉 检测到二卖点：时间={pd.to_datetime(current_kline.time)}, 价格={current_kline.close}")
    
combined_kline = combine_kline(window)
combined_k_data = [comb.data for comb in combined_kline]
fig, ax1, ax2 = create_kline_figure()
plot_kline(ax1, window, "HS300")
plot_kline(ax2, combined_k_data, "HS300")

draw_strokes(ax1, strokes)

# 打印买卖点
print("二买点:", buy_points)
print("二卖点:", sell_points)

import matplotlib.dates as mdates

def draw_2buy_2sale(ax, buy_points, sell_points):
    for point in buy_points:
        ax.plot(mdates.date2num(pd.to_datetime(point['time'], unit='s')), point['price'], 'go', markersize=8, label='二买点' if '二买点' not in ax.get_legend_handles_labels()[1] else "")
    for point in sell_points:
        ax.plot(mdates.date2num(pd.to_datetime(point['time'], unit='s')), point['price'], 'ro', markersize=8, label='二卖点' if '二卖点' not in ax.get_legend_handles_labels()[1] else "")
# 可视化结果
if kline_list:
    # mark_fractals(ax1, top_fractals, bottom_fractals)
    draw_2buy_2sale(ax1, buy_points, sell_points)
    plt.title('HS300 缠论分析与买卖点检测')
    plt.tight_layout()
    plt.show()
