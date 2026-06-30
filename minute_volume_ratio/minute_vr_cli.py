# minute_vr_cli.py - 分时量比命令行入口
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
import pandas as pd

# 兼容两种导入方式：直接运行 vs 模块导入
try:
    from minute_vr_fetcher import get_minute_data, get_prev_n_day_vol
    from minute_vr_calc import calc_avg_vol_per_minute, calc_volume_ratio, get_volume_ratio_summary
except ImportError:
    from minute_volume_ratio.minute_vr_fetcher import get_minute_data, get_prev_n_day_vol
    from minute_volume_ratio.minute_vr_calc import calc_avg_vol_per_minute, calc_volume_ratio, get_volume_ratio_summary

from day_index import init_create_client


def calc_stock_minute_vr(code, date='', n=5, client=None):
    """
    计算单只股票的分时量比数据（返回DataFrame）

    参数:
        code: 股票代码
        date: 日期，格式 '20260420'，为空则取当天
        n: 过去n个交易日，默认5
        client: 通达信客户端，为空则自动创建

    返回:
        DataFrame: 包含 time_index, cumulative_vol, volume_ratio 等列
    """
    if client is None:
        client = init_create_client()

    # 如果未指定日期，使用今天
    if not date:
        date = datetime.now().strftime('%Y%m%d')

    # Step 1: 获取分时数据
    minute_df = get_minute_data(code, date, client)
    if minute_df.empty:
        return None

    # Step 2: 获取过去n日日线成交量
    day_data = get_prev_n_day_vol(code, n, client, date)
    if not day_data:
        return None

    # Step 3: 计算每分钟均量
    avg_vol = calc_avg_vol_per_minute(day_data['vol_list'], n)

    # Step 4: 计算量比
    result_df = calc_volume_ratio(minute_df, avg_vol)

    return result_df


def iter_stocks_minute_vr(codes, date='', n=5):
    """
    迭代计算多股票的分时量比

    参数:
        codes: 股票代码列表
        date: 日期
        n: 过去n个交易日

    返回:
        Generator[(code, DataFrame)]: 每次返回一个股票代码和其量比DataFrame
    """
    client = init_create_client()
    for code in codes:
        try:
            df = calc_stock_minute_vr(code, date, n, client)
            yield (code, df)
        except Exception as e:
            print(f"[Error] {code}: {e}")
            yield (code, None)


def print_stock_minute_vr(code, date='', n=5, export_csv=False):
    """
    打印单只股票的分时量比数据

    参数:
        code: 股票代码
        date: 日期，格式 '20260420'，为空则取当天
        n: 过去n个交易日，默认5
        export_csv: 是否导出CSV
    """
    client = init_create_client()

    # 如果未指定日期，使用今天
    if not date:
        date = datetime.now().strftime('%Y%m%d')

    # Step 1: 获取分时数据
    minute_df = get_minute_data(code, date, client)
    if minute_df.empty:
        return

    # Step 2: 获取过去n日日线成交量
    day_data = get_prev_n_day_vol(code, n, client, date)
    if not day_data:
        return

    # Step 3: 计算每分钟均量
    avg_vol = calc_avg_vol_per_minute(day_data['vol_list'], n)

    # Step 4: 计算量比
    result_df = calc_volume_ratio(minute_df, avg_vol)

    # 输出
    trade_date = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
    print(f"\n股票: {code}  日期: {trade_date}  {n}日分钟均量: {avg_vol:.0f}")
    print("-" * 80)
    print(f"{'时间':<10} {'序号':>4} {'累计量':>12} {'量比':>8}")
    print("-" * 80)

    for _, row in result_df.iterrows():
        time_str = f"{int(row['hour']):02d}:{int(row['minute']):02d}"
        print(f"{time_str:<10} {int(row['time_index']):>4} {int(row['cumulative_vol']):>12} {row['volume_ratio']:>8.2f}")

    print("-" * 80)

    # 导出CSV
    if export_csv:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        output_file = os.path.join(data_dir, f"{code}_{date}_vr.csv")
        # 浮点数保留两位小数
        result_df.round(2).to_csv(output_file, index=False)
        print(f"已导出: {output_file}")


def print_stocks_minute_vr(file_path, date='', n=5):
    """
    打印批量股票的分时量比

    参数:
        file_path: 股票代码文件路径，每行一个代码
        date: 日期
        n: 过去n个交易日
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        codes = [line.strip() for line in f if line.strip()]

    print(f"共 {len(codes)} 只股票")
    for code in codes:
        try:
            print_stock_minute_vr(code, date, n)
        except Exception as e:
            print(f"[Error] {code}: {e}")


# 保留旧函数名以兼容现有代码
def run_single(code, date='', n=5, export_csv=False):
    """兼容旧接口，调用 print_stock_minute_vr"""
    return print_stock_minute_vr(code, date, n, export_csv)


def run_batch(file_path, date='', n=5):
    """兼容旧接口，调用 print_stocks_minute_vr"""
    return print_stocks_minute_vr(file_path, date, n)


# ==================== 比较接口 ====================

def compare_volume_ratio_stocks(codes, date='', n=5):
    """
    多股票量比对比

    参数:
        codes: 股票代码列表
        date: 日期
        n: 过去n个交易日

    返回:
        DataFrame: 各股票量比对比表，列包含 代码, 最大量比, 最小量比, 平均量比, 当前量比
    """
    results = []
    for code, df in iter_stocks_minute_vr(codes, date, n):
        if df is not None and not df.empty:
            summary = get_volume_ratio_summary(df)
            if summary:
                results.append({
                    '代码': code,
                    '最大量比': summary['max'],
                    '最小量比': summary['min'],
                    '平均量比': summary['avg'],
                    '当前量比': summary['current']
                })

    if not results:
        return None

    return pd.DataFrame(results)


def compare_volume_ratio_days(code, dates, n=5):
    """
    多日量比对比

    参数:
        code: 股票代码
        dates: 日期列表，如 ['20260418', '20260419', '20260420']
        n: 过去n个交易日

    返回:
        DataFrame: 多日量比对比表，列包含 日期, 最大量比, 最小量比, 平均量比, 当前量比
    """
    client = init_create_client()
    results = []

    for date in dates:
        df = calc_stock_minute_vr(code, date, n, client)
        if df is not None and not df.empty:
            summary = get_volume_ratio_summary(df)
            if summary:
                trade_date = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
                results.append({
                    '日期': trade_date,
                    '最大量比': summary['max'],
                    '最小量比': summary['min'],
                    '平均量比': summary['avg'],
                    '当前量比': summary['current']
                })

    if not results:
        return None

    return pd.DataFrame(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分时量比计算工具")
    parser.add_argument("--code", help="股票代码，如 000400")
    parser.add_argument("--date", help="日期，如 20260420，默认今天", default="")
    parser.add_argument("--n", help="过去n个交易日，默认5", type=int, default=5)
    parser.add_argument("--file", help="股票代码文件路径，每行一个代码")
    parser.add_argument("--csv", help="导出CSV", action="store_true")

    args = parser.parse_args()

    if args.file:
        print_stocks_minute_vr(args.file, args.date, args.n)
    elif args.code:
        print_stock_minute_vr(args.code, args.date, args.n, export_csv=args.csv)
    else:
        parser.print_help()