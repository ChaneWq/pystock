# strategies/vp_sync.py - 量价同步策略（滑动窗口版）
import numpy as np


def evaluate(df, window=5, sync_threshold=0.25, vr_threshold=0.8):
    """
    量价同步策略：滑动窗口扫描盘中量价齐升时段

    判断逻辑:
        1. 全天价格斜率 > 0 → 整体趋势向上
        2. 最新量比 > 阈值   → 整体偏放量
        3. 滑动窗口同步率 > 阈值 → 盘中存在量价齐升时段

    滑动窗口逻辑:
        逐段扫描 window 分钟，计算该段内:
          - 成交量斜率 > 0 (放量)
          - 价格斜率 > 0   (上涨)
        两者同时满足 → 命中一个窗口
        同步率 = 命中窗口数 / 总窗口数

    综合评分 = 价格斜率(归一化) × 同步率 × 最新量比

    参数:
        df: 分时数据 DataFrame，必须包含 price, vol, volume_ratio, time_index 列
        window: 滑动窗口大小（分钟），默认5
        sync_threshold: 同步率阈值，默认0.25
        vr_threshold: 量比阈值，默认0.8

    返回:
        dict: 策略评分结果，不满足条件返回 None
        {
            'score': float,           # 综合评分
            'price_slope': float,     # 全天价格斜率(归一化)
            'sync_rate': float,       # 滑动窗口同步率
            'latest_vr': float,       # 最新量比
            'hit_windows': int,       # 命中窗口数
            'total_windows': int,     # 总窗口数
            'hit_periods': str        # 命中时段，如 "09:30-09:34, 10:05-10:12"
        }
    """
    if df is None or len(df) < window + 1:
        return None

    price = df['price'].values
    vol = df['vol'].values
    volume_ratio = df['volume_ratio'].values
    time_index = df['time_index'].values
    hour = df['hour'].values.astype(int)
    minute = df['minute'].values.astype(int)

    # ① 全天价格斜率（归一化）
    price_slope = _slope(time_index, price) / np.mean(price)
    if price_slope <= 0:
        return None

    # ② 最新量比 > 阈值
    latest_vr = volume_ratio[-1]
    if latest_vr <= vr_threshold:
        return None

    # ③ 滑动窗口扫描
    total_windows = len(df) - window
    hit_count = 0
    hit_indices = []

    for i in range(total_windows):
        w_price = price[i:i + window]
        w_vol = vol[i:i + window]
        w_ti = np.arange(window, dtype=float)

        vol_slope = _slope(w_ti, w_vol)
        p_slope = _slope(w_ti, w_price)

        if vol_slope > 0 and p_slope > 0:
            hit_count += 1
            hit_indices.append(i)

    sync_rate = hit_count / total_windows if total_windows > 0 else 0

    if sync_rate < sync_threshold:
        return None

    # 合并连续索引为时段
    hit_periods = _merge_indices_to_periods(hit_indices, window, hour, minute)

    # 综合评分
    score = price_slope * sync_rate * latest_vr

    return {
        'score': round(score, 4),
        'price_slope': round(price_slope, 6),
        'sync_rate': round(sync_rate, 4),
        'latest_vr': round(latest_vr, 2),
        'hit_windows': hit_count,
        'total_windows': total_windows,
        'hit_periods': hit_periods,
    }


def _slope(x, y):
    """线性回归斜率"""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x * x)
    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom


def _merge_indices_to_periods(hit_indices, window, hour, minute):
    """
    将命中的窗口索引合并为连续时段

    间隔 <= 2 个窗口的视为同一时段合并，避免碎片化输出

    例: hit_indices=[0,1,2,3, 6,7,8, 50,51], window=5
    → [0,1,2,3,6,7,8] 间隔<3 合并为一段, [50,51] 单独一段
    → "09:30-09:37, 10:20-10:25"
    """
    if not hit_indices:
        return ""

    # 合并：间隔 <= 3 视为连续
    gap_threshold = 3
    groups = []
    start = hit_indices[0]
    end = hit_indices[0]
    for idx in hit_indices[1:]:
        if idx - end <= gap_threshold:
            end = idx
        else:
            groups.append((start, end))
            start = idx
            end = idx
    groups.append((start, end))

    # 转为时间字符串
    periods = []
    for s, e in groups:
        start_time = f"{hour[s]:02d}:{minute[s]:02d}"
        end_idx = e + window - 1
        end_time = f"{hour[end_idx]:02d}:{minute[end_idx]:02d}"
        periods.append(f"{start_time}-{end_time}")

    return ", ".join(periods)
