# strategies/vp_pulse.py - 量比脉冲策略
import numpy as np


def evaluate(df, pulse=2.0, min_hits=3, price_up=True, vol_up=True, merge_gap=2):
    """
    量比脉冲策略：捕捉盘中突然放量+价格上涨的脉冲上升沿

    判断逻辑:
        对每一分钟:
          ① 分钟成交量 / 5日分钟均量 ≥ pulse → 放量脉冲
          ② volume_ratio[i] > volume_ratio[i-1] → 量比递增（上升沿，vol_up=True时）
          ③ 当前价格 >= 前一分钟价格 → 价格不下跌（price_up=True时）
          三者同时满足 → 命中一个脉冲点

        合并连续脉冲点为时段（间隔 ≤ merge_gap 分钟）
        全天脉冲点数 ≥ min_hits 才算命中

    评分:
        脉冲强度 = sum(脉冲点量/均量) / 脉冲点数
        综合评分 = 脉冲强度 × 脉冲点数 × 价格斜率(归一化)

    参数:
        df: 分时数据 DataFrame，必须包含 price, vol, volume_ratio, time_index 列
        pulse: 脉冲倍数阈值，分钟量/均量 ≥ 此值才算脉冲，默认2.0
        min_hits: 最少脉冲点数，默认3
        price_up: 是否要求脉冲点价格不下跌（允许持平），默认True
        vol_up: 是否要求量比递增（只捕捉上升沿），默认True
        merge_gap: 脉冲点间隔 ≤ 此值合并为同一时段，默认2

    返回:
        dict: 策略评分结果，不满足条件返回 None
        {
            'score': float,           # 综合评分
            'pulse_intensity': float, # 脉冲强度（平均脉冲倍数）
            'hit_count': int,         # 脉冲点数
            'total_minutes': int,     # 总分钟数
            'price_slope': float,     # 全天价格斜率(归一化)
            'hit_periods': str        # 命中时段
        }
    """
    if df is None or len(df) < 2:
        return None

    price = df['price'].values
    vol = df['vol'].values
    volume_ratio = df['volume_ratio'].values
    time_index = df['time_index'].values
    hour = df['hour'].values.astype(int)
    minute = df['minute'].values.astype(int)

    # 计算每分钟的脉冲倍数（分钟量 / 5日分钟均量）
    # volume_ratio 是累计量比，这里需要用即时量比
    # 即时量比 = vol / avg_vol_per_minute
    # 从 volume_ratio 反推: cumulative_vol / time_index = 当日分钟均量
    # 但更直接的方式：avg_vol = cumulative_vol[-1] / time_index[-1] / volume_ratio[-1] * volume_ratio[-1]
    # 简单做法：用 vol / (cumulative_vol[-1] / time_index[-1]) 近似
    # 更准确：直接用 vol[i] / avg_vol，但 avg_vol 需要传入
    # 这里用 volume_ratio 的定义反推:
    # volume_ratio[i] = cumulative_vol[i] / time_index[i] / avg_vol
    # avg_vol = cumulative_vol[-1] / time_index[-1] / volume_ratio[-1]
    # 即时脉冲倍数 = vol[i] / avg_vol
    cumulative_vol_last = np.sum(vol)
    last_ti = time_index[-1]
    last_vr = volume_ratio[-1]
    if last_vr <= 0 or last_ti <= 0:
        return None
    avg_vol = cumulative_vol_last / last_ti / last_vr

    # 逐分钟扫描脉冲点（跳过第一分钟，开盘量无意义）
    hit_indices = []
    hit_ratios = []

    for i in range(1, len(df)):
        ratio = vol[i] / avg_vol
        if ratio < pulse:
            continue

        # 量比递增判断（只捕捉上升沿）
        if vol_up and volume_ratio[i] <= volume_ratio[i - 1]:
            continue

        # 价格不下跌判断（允许持平）
        if price_up and price[i] < price[i - 1]:
            continue

        hit_indices.append(i)
        hit_ratios.append(ratio)

    # 最少脉冲点数
    if len(hit_indices) < min_hits:
        return None

    # 全天价格斜率（归一化）
    price_slope = _slope(time_index, price) / np.mean(price)
    if price_slope <= 0:
        return None

    # 合并连续脉冲点为时段
    hit_periods = _merge_indices_to_periods(hit_indices, hour, minute, merge_gap)

    # 脉冲强度
    pulse_intensity = np.mean(hit_ratios)

    # 综合评分
    score = pulse_intensity * len(hit_indices) * price_slope

    return {
        'score': round(score, 4),
        'pulse_intensity': round(pulse_intensity, 2),
        'hit_count': len(hit_indices),
        'total_minutes': len(df),
        'price_slope': round(price_slope, 6),
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


def _merge_indices_to_periods(hit_indices, hour, minute, merge_gap=2):
    """
    将脉冲点索引合并为时段

    间隔 ≤ merge_gap 的视为同一时段合并
    """
    if not hit_indices:
        return ""

    groups = []
    start = hit_indices[0]
    end = hit_indices[0]
    for idx in hit_indices[1:]:
        if idx - end <= merge_gap:
            end = idx
        else:
            groups.append((start, end))
            start = idx
            end = idx
    groups.append((start, end))

    # 转为时间字符串
    periods = []
    for s, e in groups:
        start_time = "%02d:%02d" % (hour[s], minute[s])
        end_time = "%02d:%02d" % (hour[e], minute[e])
        if s == e:
            periods.append(start_time)
        else:
            periods.append("%s-%s" % (start_time, end_time))

    return ", ".join(periods)
