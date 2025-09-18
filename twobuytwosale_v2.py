import pandas as pd
from utils import (
    identify_strokes_from_klines
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

