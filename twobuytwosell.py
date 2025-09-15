import pandas as pd
from utils import (
    identify_strokes_from_pandas
)
from visualization.plot_utils import (
    create_kline_figure,
    plot_kline,
    mark_fractals,
    draw_strokes,
    draw_buy_points
)
import matplotlib.pyplot as plt

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

strokes, kline_list, combined_klines, top_fractals, bottom_fractals = identify_strokes_from_pandas(df)
combined_k_data = [comb.data for comb in combined_klines]
print(strokes)
for stroke in strokes:
    print(stroke)

fig, ax1, ax2 = create_kline_figure(figsize=(14, 10))

# 绘制原始K线（上轴）
plot_kline(ax1, kline_list, title="原始K线图（合并前）")
mark_fractals(ax1, top_fractals, bottom_fractals)  # 标记分型

# 绘制合并后K线（下轴）
plot_kline(ax2, combined_k_data, title="合并后K线图（处理包含关系）")
mark_fractals(ax2, top_fractals, bottom_fractals)  # 标记分型

draw_strokes(ax1, strokes)
draw_strokes(ax2, strokes)


def identify_buy_points(bottom_fractals, top_fractals):
    """
    识别符合条件的买点
    
    参数:
    bottom_fractals: 底分型列表
    top_fractals: 顶分型列表
    
    返回:
    buy_points: 符合条件的买点列表，每个买点包含1买点和2买点信息
    """
    buy_points = []
    i = 1  # 从第二个底分型开始检查，因为需要与前一个比较
    
    while i < len(bottom_fractals):
        # 寻找潜在的1买点：当前底分型比上一个底分型最低点更低
        current_bottom = bottom_fractals[i]
        prev_bottom = bottom_fractals[i-1]
        
        # 检查是否是潜在1买点
        if current_bottom.price < prev_bottom.price:
            potential_1_buy = {
                'type': '1买点',
                'fractal': current_bottom,
                'price': current_bottom.price,
                'index': current_bottom.klines[1].index,  # 底分型中间K线的索引
                'time': current_bottom.time
            }
            
            # 寻找有效的顶分型作为卖点
            valid_top = None
            for top in top_fractals:
                # 确保顶分型在1买点之后
                if top.klines[1].index <= potential_1_buy['index']:
                    continue
                    
                # 检查顶分型是否满足距离条件
                if abs(potential_1_buy['index'] - top.klines[1].index) >= 4:
                    # 检查1买点和顶分型之间是否有更低的底分型
                    has_lower_bottom = False
                    for b in bottom_fractals:
                        b_index = b.klines[1].index
                        # 检查是否在1买点和顶分型之间
                        if (b_index > potential_1_buy['index'] and 
                            b_index < top.klines[1].index and 
                            b.price < potential_1_buy['price']):
                            has_lower_bottom = True
                            # 更新潜在1买点为这个更低的底分型
                            potential_1_buy = {
                                'type': '1买点',
                                'fractal': b,
                                'price': b.price,
                                'index': b.klines[1].index,
                                'time': b.time
                            }
                            break  # 找到更低的就不需要继续检查了
                    
                    if not has_lower_bottom:
                        valid_top = top
                        break  # 找到有效的顶分型，退出循环
            
            # 如果没有找到符合条件的顶分型，继续寻找下一个1买点
            if valid_top is None:
                i += 1
                continue
                
            # 等待符合条件的底分型作为2买点
            valid_2_buy = None
            for next_bottom in bottom_fractals:
                next_bottom_index = next_bottom.klines[1].index
                
                # 确保2买点在顶分型之后
                if next_bottom_index <= valid_top.klines[1].index:
                    continue
                    
                # 检查底分型是否满足距离条件
                if abs(valid_top.klines[1].index - next_bottom_index) >= 4:
                    # 计算2买点价格（底分型最后一根K线的收盘价）
                    buy_price = next_bottom.klines[2].close
                    
                    potential_2_buy = {
                        'type': '2买点',
                        'fractal': next_bottom,
                        'price': buy_price,
                        'index': next_bottom_index,
                        'time': next_bottom.time
                    }
                    
                    # 检查2买点是否高于1买点
                    if potential_2_buy['price'] > potential_1_buy['price']:
                        valid_2_buy = potential_2_buy
                        break  # 找到符合条件的2买点，退出循环
            
            # 如果找到有效的2买点，添加到买点列表
            if valid_2_buy:
                buy_points.append({
                    '1_buy': potential_1_buy,
                    '2_buy': valid_2_buy,
                    'top_between': valid_top
                })
                # 从当前2买点之后继续寻找
                i = bottom_fractals.index(valid_2_buy['fractal']) + 1
                continue
        
        # 继续检查下一个底分型
        i += 1
    
    return buy_points

# 使用策略识别买点
buy_points = identify_buy_points(bottom_fractals, top_fractals)

# 输出识别到的买点
print(f"\n识别到 {len(buy_points)} 个符合条件的买点组合：")
for i, bp in enumerate(buy_points, 1):
    print(f"\n买点组合 {i}:")
    print(f"1买点: 位置={bp['1_buy']['index']}, 价格={bp['1_buy']['price']}")
    print(f"中间顶分型: 位置={bp['top_between'].klines[1].index}")
    print(f"2买点: 位置={bp['2_buy']['index']}, 价格={bp['2_buy']['price']}")

# 在两个图表上都标记买点
draw_buy_points(ax1, buy_points)
draw_buy_points(ax2, buy_points)

# 添加图例并显示更新后的图像
ax1.legend()
ax2.legend()
plt.tight_layout()

plt.show()
print("✅ 可视化完成！")


print("\n✅ 策略分析完成！")