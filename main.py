# main.py
import pandas as pd
from datetime import datetime
from core.Chan_base import KLine
from utils import (
    combine_kline,
    detect_fractals,
    find_all_necessary_points,
    print_necessary_points,
    identify_strokes,
    identify_strokes_from_necessary_points
)
from visualization.plot_utils import (
    create_kline_figure,
    plot_kline,
    mark_fractals,
    draw_strokes
)
import matplotlib.pyplot as plt


def load_data(file_path, tail_n=50):
    """读取CSV格式的K线数据，返回DataFrame"""
    try:
        df = pd.read_csv(file_path)
        # 保留最后N条数据（避免数据量过大）
        df = df.tail(tail_n)
        # 转换日期格式（确保后续能转时间戳）
        df['date'] = pd.to_datetime(df['date'])
        print(f"✅ 成功读取数据：{len(df)}条记录，时间范围：{df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
        return df
    except Exception as e:
        print(f"❌ 数据读取失败：{str(e)}")
        print("请检查文件路径是否正确，或CSV格式是否包含'date,open,high,low,close,volume'列")
        raise


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


def print_necessary_points(points):
    """打印必经点信息（便于调试）"""
    if not points:
        print("❌ 未找到任何必经点")
        return
    print("\n📌 所有必经点信息：")
    for i, point in enumerate(points, 1):
        fractal = point["fractal"]
        time_str = datetime.fromtimestamp(fractal.time).strftime("%Y-%m-%d")
        print(f"  第{i}个必经点：")
        print(f"    - 类型：{'初始必经点' if point['type'] == 'initial' else '递归必经点'}")
        print(f"    - 分型：{'顶分型' if point['top_or_bottom'] == 'top' else '底分型'}")
        print(f"    - 时间：{time_str}")
        print(f"    - 价格：{fractal.price:.2f}")
        print(f"    - 分段：{point['segment_type']}")


def main():
    # -------------------------- 1. 配置参数 --------------------------
    DATA_PATH = "data/hs300_k_data_week.csv"  # 数据文件路径（根据实际情况修改）
    TAKE_TAIL_N = 200  # 保留最后N条数据

    # -------------------------- 2. 数据加载与转换 --------------------------
    print("=" * 50)
    print("1. 数据加载与转换")
    print("=" * 50)
    df = load_data(DATA_PATH, TAKE_TAIL_N)
    kline_list = df_to_kline_list(df)

    # -------------------------- 3. K线合并 --------------------------
    print("\n" + "=" * 50)
    print("2. K线合并（处理包含关系）")
    print("=" * 50)
    combined_klines = combine_kline(kline_list)
    combined_k_data = [comb.data for comb in combined_klines]  # 提取合并后的KLine对象
    print(f"✅ 合并前K线数量：{len(kline_list)}")
    print(f"✅ 合并后K线数量：{len(combined_k_data)}")

    # 打印combined_klines
    print("\n" + "=" * 50)
    print("3. 打印combined_klines")
    print("=" * 50)
    for kline in combined_klines:
        print(kline)

    # -------------------------- 4. 分型检测 --------------------------
    print("\n" + "=" * 50)
    print("3. 分型检测（顶分型+底分型）")
    print("=" * 50)
    top_fractals, bottom_fractals = detect_fractals(combined_klines)
    print(f"✅ 检测到顶分型数量：{len(top_fractals)}")
    print(f"✅ 检测到底分型数量：{len(bottom_fractals)}")

    # -------------------------- 5. 必经点查找 --------------------------
    print("\n" + "=" * 50)
    print("4. 必经点查找（初始+递归）")
    print("=" * 50)
    all_necessary_points = find_all_necessary_points(combined_klines, top_fractals, bottom_fractals)
    print_necessary_points(all_necessary_points)

    strokes = identify_strokes_from_necessary_points(combined_klines, top_fractals, bottom_fractals, all_necessary_points[0]["fractal"], all_necessary_points[1]["fractal"])

    print(strokes)

    # -------------------------- 6. 笔识别 --------------------------
    print("\n" + "=" * 50)
    print("5. 笔识别（基于必经点）")
    print("=" * 50)
    identified_strokes = identify_strokes(combined_klines,all_necessary_points, top_fractals, bottom_fractals)

    print(identified_strokes)

    # -------------------------- 7. 可视化 --------------------------
    print("\n" + "=" * 50)
    print("6. 结果可视化（生成K线图）")
    print("=" * 50)
    # 创建双轴图（原始K线+合并后K线）
    fig, ax1, ax2 = create_kline_figure(figsize=(14, 10))

    # 绘制原始K线（上轴）
    plot_kline(ax1, kline_list, title="原始K线图（合并前）")
    mark_fractals(ax1, top_fractals, bottom_fractals)  # 标记分型

    # 绘制合并后K线（下轴）
    plot_kline(ax2, combined_k_data, title="合并后K线图（处理包含关系）")
    mark_fractals(ax2, top_fractals, bottom_fractals)  # 标记分型

    draw_strokes(ax1, identified_strokes)
    draw_strokes(ax2, identified_strokes)

    # 显示图像
    plt.tight_layout()  # 自动调整布局
    plt.show()
    print("✅ 可视化完成！")


if __name__ == "__main__":
    main()
