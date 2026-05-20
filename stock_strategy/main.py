# main.py - 策略扫描入口
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
from strategies import list_strategies
from scanner import scan, print_results, export_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="强势股策略扫描工具")

    # 通用参数
    parser.add_argument("--strategy", help="策略ID，可用: %s" % list_strategies(), required=True)
    parser.add_argument("--file", help="股票代码文件路径，每行一个代码", required=True)
    parser.add_argument("--date", help="日期，格式 YYYYMMDD，默认今天", default="")
    parser.add_argument("--n", help="过去n个交易日，默认5", type=int, default=5)
    parser.add_argument("--csv", help="导出CSV到data目录", action="store_true")
    parser.add_argument("--until", help="截至时间，格式 HH:MM，模拟盘中该时间点运行，如 --until 10:30", default="")
    parser.add_argument("--no_filter", help="不过滤创业板(300/301)、科创板(688)、北交所(9开头)等", action="store_true", default=False)
    parser.add_argument("--change_min", help="涨幅下限(%%)，默认-100不限", type=float, default=-100)
    parser.add_argument("--change_max", help="涨幅上限(%%)，默认100不限", type=float, default=100)

    # vp_sync 策略参数
    parser.add_argument("--window", help="[vp_sync] 滑动窗口大小（分钟），默认5", type=int, default=5)
    parser.add_argument("--sync_threshold", help="[vp_sync] 同步率阈值，默认0.25", type=float, default=0.25)
    parser.add_argument("--vr_threshold", help="[vp_sync] 量比阈值，默认0.8", type=float, default=0.8)

    # vp_pulse 策略参数
    parser.add_argument("--pulse", help="[vp_pulse] 脉冲倍数阈值，分钟量/均量>=此值才算脉冲，默认2.0", type=float, default=2.0)
    parser.add_argument("--min_hits", help="[vp_pulse] 最少脉冲点数，默认3", type=int, default=3)
    parser.add_argument("--price_up", help="[vp_pulse] 脉冲点是否要求价格上涨，默认True", action="store_true", default=True)
    parser.add_argument("--no_price_up", help="[vp_pulse] 脉冲点不要求价格上涨", action="store_true", default=False)
    parser.add_argument("--no_vol_up", help="[vp_pulse] 脉冲点不要求量比递增（捕捉下降沿）", action="store_true", default=False)
    parser.add_argument("--merge_gap", help="[vp_pulse] 脉冲点间隔<=此值合并为同一时段，默认2", type=int, default=2)

    # vr_slope 策略参数
    parser.add_argument("--vr_slope_window", help="[vr_slope] 窗口大小（分钟），默认3", type=int, default=3)
    parser.add_argument("--vr_slope", help="[vr_slope] 量比斜率角度阈值（度），默认5度", type=float, default=5)
    parser.add_argument("--no_vr_up", help="[vr_slope] 不要求窗口首尾量比增加", action="store_true", default=False)
    parser.add_argument("--vr_slope_price_up", help="[vr_slope] 窗口首尾价格不下跌，默认True", action="store_true", default=True)
    parser.add_argument("--no_vr_slope_price_up", help="[vr_slope] 不要求窗口首尾价格上涨", action="store_true", default=False)
    parser.add_argument("--vr_slope_min_hits", help="[vr_slope] 最少命中窗口数，默认3", type=int, default=3)
    parser.add_argument("--vr_slope_merge_gap", help="[vr_slope] 命中窗口间隔<=此值合并，默认2", type=int, default=2)

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
    if args.strategy == 'vp_pulse':
        price_up = not args.no_price_up
        vol_up = not args.no_vol_up
        strategy_kwargs = {
            'pulse': args.pulse,
            'min_hits': args.min_hits,
            'price_up': price_up,
            'vol_up': vol_up,
            'merge_gap': args.merge_gap,
        }
        print("策略: %s  日期: %s  股票数: %d  脉冲阈值: %.1f  最少脉冲点: %d  价格上涨: %s  量比递增: %s  合并间隔: %d%s" % (
            args.strategy, date, len(codes), args.pulse, args.min_hits, price_up, vol_up, args.merge_gap,
            "  截至时间: %s" % args.until if args.until else ""))
    elif args.strategy == 'vp_sync':
        strategy_kwargs = {
            'window': args.window,
            'sync_threshold': args.sync_threshold,
            'vr_threshold': args.vr_threshold,
        }
        print("策略: %s  日期: %s  股票数: %d  窗口: %d分钟  同步阈值: %.2f  量比阈值: %.1f%s" % (
            args.strategy, date, len(codes), args.window, args.sync_threshold, args.vr_threshold,
            "  截至时间: %s" % args.until if args.until else ""))
    elif args.strategy == 'vr_slope':
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
        print("策略: %s  日期: %s  股票数: %d  窗口: %d分钟  量比斜率: %.0f度  量比增加: %s  价格上涨: %s  最少命中: %d  合并间隔: %d%s" % (
            args.strategy, date, len(codes), args.vr_slope_window, args.vr_slope, vr_up, vr_price_up,
            args.vr_slope_min_hits, args.vr_slope_merge_gap,
            "  截至时间: %s" % args.until if args.until else ""))
    else:
        strategy_kwargs = {}

    # 扫描
    results = scan(codes, date, args.strategy, args.n, until_hour=until_hour, until_minute=until_minute,
                   change_min=args.change_min, change_max=args.change_max, **strategy_kwargs)

    # 输出
    print_results(results, args.strategy, date)

    # 导出
    if args.csv:
        export_results(results, args.strategy, date)
