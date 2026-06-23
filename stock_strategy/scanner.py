# scanner.py - 扫描引擎
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from day_index import init_create_client
from minute_volume_ratio.minute_vr_fetcher import get_minute_data, get_prev_n_day_vol
from minute_volume_ratio.minute_vr_calc import calc_avg_vol_per_minute, calc_volume_ratio
from strategies import get_strategy


def _load_stock_names():
    """加载股票名称对照表"""
    name_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'data', '全部Ａ股个股.csv')
    if not os.path.exists(name_file):
        return {}
    df = pd.read_csv(name_file, dtype={'代码': str}, encoding='utf-8')
    return dict(zip(df['代码'], df['名称']))


def scan(codes, date, strategy_id, n=5, until_hour=None, until_minute=None, change_min=-100, change_max=100, **strategy_kwargs):
    """
    扫描股票列表，按策略评分

    参数:
        codes: 股票代码列表
        date: 日期，格式 '20260519'
        strategy_id: 策略ID
        n: 过去n个交易日，默认5
        until_hour: 截至时间-小时，None表示全天
        until_minute: 截至时间-分钟，None表示全天
        change_min: 涨幅下限(%)，默认-100不限
        change_max: 涨幅上限(%)，默认100不限
        **strategy_kwargs: 策略参数，透传给策略的evaluate函数

    返回:
        list[dict]: 命中结果，按 score 降序排列
    """
    strategy_fn = get_strategy(strategy_id)
    client = init_create_client()
    stock_names = _load_stock_names()
    results = []

    total = len(codes)
    for i, code in enumerate(codes):
        print(f"\r扫描中: {i+1}/{total} {code}", end='', flush=True)
        try:
            result = _scan_single(code, date, client, strategy_fn, n, until_hour, until_minute,
                                  change_min, change_max, stock_names, **strategy_kwargs)
            if result is not None:
                results.append(result)
        except Exception as e:
            print(f"\n[Error] {code}: {e}")

    print()  # 换行

    # 按综合评分降序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def _scan_single(code, date, client, strategy_fn, n, until_hour=None, until_minute=None,
                 change_min=-100, change_max=100, stock_names=None, **strategy_kwargs):
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
    day_data = get_prev_n_day_vol(code, n, client, date=date)
    if not day_data:
        return None

    # 计算量比
    avg_vol = calc_avg_vol_per_minute(day_data['vol_list'], n)
    result_df = calc_volume_ratio(minute_df, avg_vol)

    # 执行策略评估
    eval_result = strategy_fn(result_df, **strategy_kwargs)
    if eval_result is None:
        return None

    # 计算涨幅
    prev_close = day_data['prev_close']
    latest_price = result_df['price'].iloc[-1]
    change_pct = (latest_price - prev_close) / prev_close * 100

    # 涨幅范围过滤
    if change_pct < change_min or change_pct > change_max:
        return None

    eval_result['code'] = code
    eval_result['name'] = stock_names.get(code, '') if stock_names else ''
    eval_result['date'] = date
    eval_result['change_pct'] = round(change_pct, 2)
    return eval_result


def print_results(results, strategy_id, date):
    """打印扫描结果"""
    if not results:
        print(f"\n策略: {strategy_id}  日期: {date}  命中: 0只")
        return

    print(f"\n策略: {strategy_id}  日期: {date}  命中: {len(results)}只")

    if strategy_id == 'vr_anomaly':
        _print_anomaly(results, strategy_id, date)
    else:
        _print_slope(results, strategy_id, date)


def _print_slope(results, strategy_id, date):
    """vr_slope 策略输出"""
    print("-" * 140)
    print(f"{'排名':>4}  {'代码':<8}  {'名称':<8}  {'综合评分':>8}  {'量比斜率':>8}  {'命中窗口':>8}  {'涨幅':>8}  {'价格斜率':>10}  {'命中时段'}")
    print("-" * 140)

    for i, r in enumerate(results):
        chg = r['change_pct']
        chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"
        print(f"{i+1:>4}  {r['code']:<8}  {r['name']:<8}  {r['score']:>8.4f}  {r['avg_vr_slope_deg']:>6.1f}°  "
              f"{r['hit_windows']:>4}/{r['total_windows']}  {chg_str:>8}  {r['price_slope']:>10.6f}  {r['hit_periods']}")

    print("-" * 140)


def _print_anomaly(results, strategy_id, date):
    """vr_anomaly 策略输出"""
    print("-" * 150)
    print(f"{'排名':>4}  {'代码':<8}  {'名称':<8}  {'综合评分':>8}  {'显性':>4}  {'隐性':>4}  {'最大角度差':>8}  {'涨幅':>8}  {'命中时段'}")
    print("-" * 150)

    for i, r in enumerate(results):
        chg = r['change_pct']
        chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"
        print(f"{i+1:>4}  {r['code']:<8}  {r['name']:<8}  {r['score']:>8.4f}  {r['steep_hits']:>4}  {r['turn_hits']:>4}  "
              f"{r['max_angle_diff']:>7.1f}°  {chg_str:>8}  {r['hit_periods']}")

    print("-" * 150)


def export_results(results, strategy_id, date):
    """导出结果到CSV"""
    if not results:
        print("无命中结果，不导出")
        return

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    output_file = os.path.join(data_dir, f"{strategy_id}_{date}.csv")

    # 重命名列并指定顺序
    if strategy_id == 'vr_anomaly':
        col_order = ['代码', '名称', '涨幅%', '显性命中', '隐性命中', '最大角度差', '综合评分', '命中窗口', '总窗口', '价格斜率', '命中时段', '日期']
        rename_map = {
            'score': '综合评分',
            'steep_hits': '显性命中',
            'turn_hits': '隐性命中',
            'max_angle_diff': '最大角度差',
            'hit_windows': '命中窗口',
            'total_windows': '总窗口',
            'price_slope': '价格斜率',
            'hit_periods': '命中时段',
            'name': '名称',
            'code': '代码',
            'date': '日期',
            'change_pct': '涨幅%',
        }
    else:
        col_order = ['代码', '名称', '涨幅%', '量比斜率(度)', '综合评分', '命中窗口', '总窗口', '价格斜率', '命中时段', '日期']
        rename_map = {
            'score': '综合评分',
            'avg_vr_slope_deg': '量比斜率(度)',
            'hit_windows': '命中窗口',
            'total_windows': '总窗口',
            'price_slope': '价格斜率',
            'hit_periods': '命中时段',
            'name': '名称',
            'code': '代码',
            'date': '日期',
            'change_pct': '涨幅%',
        }
    df = pd.DataFrame(results)
    df = df.rename(columns=rename_map)
    df = df[col_order]
    df.to_csv(output_file, index=False)
    print(f"已导出: {output_file}")


def export_codes(results, strategy_id, date):
    """导出命中个股代码到文件"""
    if not results:
        print("无命中结果，不导出代码")
        return

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, f"{strategy_id}_{date}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(r['code'] + '\n')
    print(f"已导出代码: {output_file} ({len(results)}只)")
