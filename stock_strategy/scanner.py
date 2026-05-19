# scanner.py - 扫描引擎
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from day_index import init_create_client
from minute_volume_ratio.fetcher import get_minute_data, get_prev_n_day_vol
from minute_volume_ratio.calculator import calc_avg_vol_per_minute, calc_volume_ratio
from strategies import get_strategy


def scan(codes, date, strategy_id, n=5, until_hour=None, until_minute=None, **strategy_kwargs):
    """
    扫描股票列表，按策略评分

    参数:
        codes: 股票代码列表
        date: 日期，格式 '20260519'
        strategy_id: 策略ID
        n: 过去n个交易日，默认5
        until_hour: 截至时间-小时，None表示全天
        until_minute: 截至时间-分钟，None表示全天
        **strategy_kwargs: 策略参数，透传给策略的evaluate函数

    返回:
        list[dict]: 命中结果，按 score 降序排列
    """
    strategy_fn = get_strategy(strategy_id)
    client = init_create_client()
    results = []

    total = len(codes)
    for i, code in enumerate(codes):
        print(f"\r扫描中: {i+1}/{total} {code}", end='', flush=True)
        try:
            result = _scan_single(code, date, client, strategy_fn, n, until_hour, until_minute, **strategy_kwargs)
            if result is not None:
                results.append(result)
        except Exception as e:
            print(f"\n[Error] {code}: {e}")

    print()  # 换行

    # 按综合评分降序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def _scan_single(code, date, client, strategy_fn, n, until_hour=None, until_minute=None, **strategy_kwargs):
    """扫描单只股票"""
    # 获取分时数据
    minute_df = get_minute_data(code, date, client)
    if minute_df.empty:
        return None

    # 截至时间截断
    if until_hour is not None and until_minute is not None:
        mask = (minute_df['hour'].astype(int) < until_hour) | \
               ((minute_df['hour'].astype(int) == until_hour) & (minute_df['minute'].astype(int) <= until_minute))
        minute_df = minute_df[mask].reset_index(drop=True)
        if minute_df.empty:
            return None

    # 获取过去n日成交量
    day_vol_list = get_prev_n_day_vol(code, n, client)
    if not day_vol_list:
        return None

    # 计算量比
    avg_vol = calc_avg_vol_per_minute(day_vol_list, n)
    result_df = calc_volume_ratio(minute_df, avg_vol)

    # 执行策略评估
    eval_result = strategy_fn(result_df, **strategy_kwargs)
    if eval_result is None:
        return None

    eval_result['code'] = code
    eval_result['date'] = date
    return eval_result


def print_results(results, strategy_id, date):
    """打印扫描结果"""
    if not results:
        print(f"\n策略: {strategy_id}  日期: {date}  命中: 0只")
        return

    print(f"\n策略: {strategy_id}  日期: {date}  命中: {len(results)}只")

    # 根据策略动态选择列
    sample = results[0]
    if strategy_id == 'vp_pulse':
        _print_pulse(results, strategy_id, date)
    elif strategy_id == 'vr_slope':
        _print_vr_slope(results, strategy_id, date)
    else:
        _print_sync(results, strategy_id, date)


def _print_pulse(results, strategy_id, date):
    """vp_pulse 策略输出"""
    print("-" * 120)
    print(f"{'排名':>4}  {'代码':<8}  {'综合评分':>8}  {'脉冲强度':>8}  {'脉冲点':>8}  {'价格斜率':>10}  {'命中时段'}")
    print("-" * 120)

    for i, r in enumerate(results):
        print(f"{i+1:>4}  {r['code']:<8}  {r['score']:>8.4f}  {r['pulse_intensity']:>8.2f}  "
              f"{r['hit_count']:>4}/{r['total_minutes']}  {r['price_slope']:>10.6f}  {r['hit_periods']}")

    print("-" * 120)


def _print_vr_slope(results, strategy_id, date):
    """vr_slope 策略输出"""
    print("-" * 120)
    print(f"{'排名':>4}  {'代码':<8}  {'综合评分':>8}  {'量比斜率':>8}  {'命中窗口':>8}  {'价格斜率':>10}  {'命中时段'}")
    print("-" * 120)

    for i, r in enumerate(results):
        print(f"{i+1:>4}  {r['code']:<8}  {r['score']:>8.4f}  {r['avg_vr_slope_deg']:>6.1f}°  "
              f"{r['hit_windows']:>4}/{r['total_windows']}  {r['price_slope']:>10.6f}  {r['hit_periods']}")

    print("-" * 120)


def _print_sync(results, strategy_id, date):
    """vp_sync 策略输出"""
    print("-" * 120)
    print(f"{'排名':>4}  {'代码':<8}  {'综合评分':>8}  {'价格斜率':>10}  {'同步率':>6}  {'最新量比':>8}  {'命中窗口':>8}  {'命中时段'}")
    print("-" * 120)

    for i, r in enumerate(results):
        print(f"{i+1:>4}  {r['code']:<8}  {r['score']:>8.4f}  {r['price_slope']:>10.6f}  "
              f"{r['sync_rate']:>6.4f}  {r['latest_vr']:>8.2f}  {r['hit_windows']:>4}/{r['total_windows']}  {r['hit_periods']}")

    print("-" * 120)


def export_results(results, strategy_id, date):
    """导出结果到CSV"""
    if not results:
        print("无命中结果，不导出")
        return

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    output_file = os.path.join(data_dir, f"{strategy_id}_{date}.csv")
    df = pd.DataFrame(results)
    df.round(4).to_csv(output_file, index=False)
    print(f"已导出: {output_file}")
