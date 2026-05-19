# main.py - 量比计算入口
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
from fetcher import get_minute_data, get_prev_n_day_vol
from calculator import calc_avg_vol_per_minute, calc_volume_ratio
from day_index import init_create_client


def run_single(code, date='', n=5, export_csv=False):
    """
    计算单只股票的量比数据

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
    day_vol_list = get_prev_n_day_vol(code, n, client)
    if not day_vol_list:
        return

    # Step 3: 计算每分钟均量
    avg_vol = calc_avg_vol_per_minute(day_vol_list, n)

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


def run_batch(file_path, date='', n=5):
    """
    批量计算股票量比

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
            run_single(code, date, n)
        except Exception as e:
            print(f"[Error] {code}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分时量比计算工具")
    parser.add_argument("--code", help="股票代码，如 000400")
    parser.add_argument("--date", help="日期，如 20260420，默认今天", default="")
    parser.add_argument("--n", help="过去n个交易日，默认5", type=int, default=5)
    parser.add_argument("--file", help="股票代码文件路径，每行一个代码")
    parser.add_argument("--csv", help="导出CSV", action="store_true")

    args = parser.parse_args()

    if args.file:
        run_batch(args.file, args.date, args.n)
    elif args.code:
        run_single(args.code, args.date, args.n, export_csv=args.csv)
    else:
        parser.print_help()
