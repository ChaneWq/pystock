# main.py - 策略扫描入口
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
from scanner import scan, print_results, export_results, export_codes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="量比斜率策略扫描工具")

    # 通用参数
    parser.add_argument("--file", help="股票代码文件路径，每行一个代码", required=True)
    parser.add_argument("--date", help="日期，格式 YYYYMMDD，默认今天", default="")
    parser.add_argument("--n", help="过去n个交易日，默认5", type=int, default=5)
    parser.add_argument("--csv", help="导出CSV到data目录", action="store_true")
    parser.add_argument("--output", help="导出命中个股代码到output目录", action="store_true")
    parser.add_argument("--until", help="截至时间，格式 HH:MM，模拟盘中该时间点运行，如 --until 10:30", default="")
    parser.add_argument("--no_filter", help="不过滤创业板(300/301)、科创板(688)、北交所(9开头)等", action="store_true", default=False)
    parser.add_argument("--change_min", help="涨幅下限(%%)，默认-100不限", type=float, default=-100)
    parser.add_argument("--change_max", help="涨幅上限(%%)，默认100不限", type=float, default=100)

    # vr_slope 策略参数
    parser.add_argument("--vr_slope_window", help="窗口大小（分钟），默认3", type=int, default=3)
    parser.add_argument("--vr_slope", help="量比斜率角度阈值（度），默认5度", type=float, default=5)
    parser.add_argument("--no_vr_up", help="不要求窗口首尾量比增加", action="store_true", default=False)
    parser.add_argument("--vr_slope_price_up", help="窗口首尾价格不下跌，默认True", action="store_true", default=True)
    parser.add_argument("--no_vr_slope_price_up", help="不要求窗口首尾价格上涨", action="store_true", default=False)
    parser.add_argument("--vr_slope_min_hits", help="最少命中窗口数，默认3", type=int, default=3)
    parser.add_argument("--vr_slope_merge_gap", help="命中窗口间隔<=此值合并，默认2", type=int, default=2)

    args = parser.parse_args()

    # 日期
    date = args.date or datetime.now().strftime('%Y%m%d')

    # 解析截至时间
    until_hour = None
    until_minute = None
    if args.until:
        try:
            parts = args.until.split(':')
            until_hour = int(parts[0])
            until_minute = int(parts[1])
        except (ValueError, IndexError):
            print("截至时间格式错误，应为 HH:MM，如 10:30")
            sys.exit(1)

    # 读取股票列表
    if not os.path.exists(args.file):
        print("文件不存在: %s" % args.file)
        sys.exit(1)

    with open(args.file, 'r', encoding='utf-8') as f:
        codes = [line.strip() for line in f if line.strip()]

    if not codes:
        print("股票列表为空")
        sys.exit(1)

    # 过滤创业板/科创板/北交所
    if not args.no_filter:
        filter_prefixes = ('300', '301', '688', '9')
        original_count = len(codes)
        codes = [c for c in codes if not c.startswith(filter_prefixes)]
        filtered_count = original_count - len(codes)
        if filtered_count > 0:
            print("已过滤 %d 只（创业板/科创板/北交所），剩余 %d 只" % (filtered_count, len(codes)))

    if not codes:
        print("过滤后股票列表为空")
        sys.exit(1)

    # 构建策略参数
    vr_price_up = not args.no_vr_slope_price_up
    vr_up = not args.no_vr_up
    strategy_kwargs = {
        'window': args.vr_slope_window,
        'vr_slope': args.vr_slope,
        'vr_up': vr_up,
        'price_up': vr_price_up,
        'min_hits': args.vr_slope_min_hits,
        'merge_gap': args.vr_slope_merge_gap,
    }
    print("策略: vr_slope  日期: %s  股票数: %d  窗口: %d分钟  量比斜率: %.0f度  量比增加: %s  价格上涨: %s  最少命中: %d  合并间隔: %d%s" % (
        date, len(codes), args.vr_slope_window, args.vr_slope, vr_up, vr_price_up,
        args.vr_slope_min_hits, args.vr_slope_merge_gap,
        "  截至时间: %s" % args.until if args.until else ""))

    # 扫描
    results = scan(codes, date, 'vr_slope', args.n, until_hour=until_hour, until_minute=until_minute,
                   change_min=args.change_min, change_max=args.change_max, **strategy_kwargs)

    # 输出
    print_results(results, 'vr_slope', date)

    # 导出
    if args.csv:
        export_results(results, 'vr_slope', date)

    # 导出代码
    if args.output:
        export_codes(results, 'vr_slope', date)
