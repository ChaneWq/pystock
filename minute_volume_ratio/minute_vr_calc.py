# minute_vr_calc.py - 分时量比核心计算层
import numpy as np


# ==================== 基础计算函数 ====================

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


# ==================== 查询接口 ====================

def get_volume_ratio_at_time(df, hour, minute):
    """
    获取指定时间点的量比

    参数:
        df: 包含 volume_ratio, hour, minute 列的 DataFrame
        hour: 小时 (int)
        minute: 分钟 (int)

    返回:
        float: 该时间点的量比，未找到返回 None
    """
    mask = (df['hour'].astype(int) == hour) & (df['minute'].astype(int) == minute)
    if mask.any():
        return float(df.loc[mask, 'volume_ratio'].iloc[0])
    return None


def get_volume_ratio_range(df, start_time, end_time):
    """
    获取时间段内的量比数据

    参数:
        df: 包含 volume_ratio, hour, minute 列的 DataFrame
        start_time: 开始时间，格式 'HH:MM' 或 '09:30'
        end_time: 结束时间，格式 'HH:MM' 或 '11:30'

    返回:
        DataFrame: 该时间段内的数据
    """
    start_h, start_m = map(int, start_time.split(':'))
    end_h, end_m = map(int, end_time.split(':'))

    # 构建时间序号
    start_idx = calc_time_index(start_h, start_m)
    end_idx = calc_time_index(end_h, end_m)

    mask = (df['time_index'] >= start_idx) & (df['time_index'] <= end_idx)
    return df[mask].reset_index(drop=True)


def get_current_volume_ratio(df):
    """
    获取最新（最后一分钟）的量比

    参数:
        df: 包含 volume_ratio 列的 DataFrame

    返回:
        float: 最新量比
    """
    if df.empty:
        return None
    return float(df['volume_ratio'].iloc[-1])


# ==================== 统计接口 ====================

def get_volume_ratio_summary(df):
    """
    获取量比统计摘要

    参数:
        df: 包含 volume_ratio 列的 DataFrame

    返回:
        dict: {'max': 最大量比, 'min': 最小量比, 'avg': 平均量比, 'current': 当前量比}
    """
    if df.empty:
        return None

    vr = df['volume_ratio']
    return {
        'max': float(vr.max()),
        'min': float(vr.min()),
        'avg': float(vr.mean()),
        'current': float(vr.iloc[-1])
    }


def get_volume_ratio_trend(df, window=10):
    """
    判断量比趋势

    参数:
        df: 包含 volume_ratio 列的 DataFrame
        window: 判断窗口大小（分钟），默认10

    返回:
        str: '上升' / '下降' / '平稳'
    """
    if len(df) < window:
        return '数据不足'

    recent = df['volume_ratio'].tail(window)
    slope = (recent.iloc[-1] - recent.iloc[0]) / (window - 1)

    if slope > 0.05:
        return '上升'
    elif slope < -0.05:
        return '下降'
    else:
        return '平稳'


# ==================== 过滤接口 ====================

def filter_volume_ratio_by_range(df, min_vr=None, max_vr=None):
    """
    按量比范围过滤时段

    参数:
        df: 包含 volume_ratio 列的 DataFrame
        min_vr: 量比下限，None 表示不限
        max_vr: 量比上限，None 表示不限

    返回:
        DataFrame: 符合条件的时段
    """
    mask = True
    if min_vr is not None:
        mask = mask & (df['volume_ratio'] >= min_vr)
    if max_vr is not None:
        mask = mask & (df['volume_ratio'] <= max_vr)
    return df[mask].reset_index(drop=True)


def find_volume_ratio_peaks(df, threshold=3.0):
    """
    查找量比峰值时段

    参数:
        df: 包含 volume_ratio, hour, minute 列的 DataFrame
        threshold: 量比阈值，默认3.0

    返回:
        list: [(时间, 量比), ...] 按量比降序排列
    """
    high_vr = filter_volume_ratio_by_range(df, min_vr=threshold)
    if high_vr.empty:
        return []

    peaks = []
    for _, row in high_vr.iterrows():
        time_str = f"{int(row['hour']):02d}:{int(row['minute']):02d}"
        peaks.append((time_str, float(row['volume_ratio'])))

    # 按量比降序排列
    peaks.sort(key=lambda x: x[1], reverse=True)
    return peaks


def find_volume_ratio_breakout(df, threshold=2.0, prev_window=5):
    """
    查找量比突破时段（从低位突破阈值）

    参数:
        df: 包含 volume_ratio 列的 DataFrame
        threshold: 突破阈值，默认2.0
        prev_window: 前置窗口大小，默认5分钟

    返回:
        list: [(时间, 前量比, 后量比), ...]
    """
    if len(df) < prev_window + 1:
        return []

    breakouts = []
    vr = df['volume_ratio'].values

    for i in range(prev_window, len(df)):
        if vr[i] >= threshold:
            # 检查前窗口平均量比是否低于阈值
            prev_avg = np.mean(vr[i - prev_window:i])
            if prev_avg < threshold:
                time_str = f"{int(df['hour'].iloc[i]):02d}:{int(df['minute'].iloc[i]):02d}"
                breakouts.append((time_str, round(prev_avg, 2), round(vr[i], 2)))

    return breakouts