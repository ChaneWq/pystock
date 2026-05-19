# calculator.py - 量比核心计算层
import numpy as np


def calc_time_index(hour, minute):
    """
    计算时间序号（通达信公式）
    时间序号:=IF(HOUR>12,(HOUR-13)*60+MINUTE+120,(HOUR-9)*60+MINUTE-30)+1

    参数:
        hour: 小时 (int 或 array)
        minute: 分钟 (int 或 array)

    返回:
        时间序号 1~240

    验证:
        9:30  → (9-9)*60+30-30+1 = 1
        11:29 → (11-9)*60+29-30+1 = 120
        13:00 → (13-13)*60+0+120+1 = 121
        14:59 → (14-13)*60+59+120+1 = 240
    """
    hour = np.array(hour)
    minute = np.array(minute)
    # 向量化计算
    morning = (hour - 9) * 60 + minute - 30
    afternoon = (hour - 13) * 60 + minute + 120
    result = np.where(hour > 12, afternoon, morning) + 1
    return result


def calc_avg_vol_per_minute(day_vol_list, n=5):
    """
    计算过去n日每分钟平均成交量（对应通达信 DYNAINFO(16)）

    公式: sum(过去n日成交量) / (n * 240)

    参数:
        day_vol_list: 过去n个交易日的成交量列表
        n: 交易日天数

    返回:
        float: 每分钟平均成交量
    """
    total_vol = sum(day_vol_list[-n:])
    return total_vol / (n * 240)


def calc_volume_ratio(minute_df, avg_vol_per_minute):
    """
    计算每一分钟的量比

    量比 = 当日累计成交量 / 时间序号 / 过去5日每分钟均量

    参数:
        minute_df: 分时数据 DataFrame，必须包含 vol, hour, minute 列
        avg_vol_per_minute: 过去5日每分钟平均成交量

    返回:
        DataFrame，新增列: time_index, cumulative_vol, volume_ratio
    """
    df = minute_df.copy()

    # 计算时间序号
    df['time_index'] = calc_time_index(df['hour'].values, df['minute'].values)

    # 计算累计成交量
    df['cumulative_vol'] = df['vol'].cumsum()

    # 计算量比
    df['volume_ratio'] = df['cumulative_vol'] / df['time_index'] / avg_vol_per_minute

    # 保留2位小数
    df['volume_ratio'] = df['volume_ratio'].round(2)

    return df
