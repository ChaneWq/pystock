# main_v2.py - 配置式策略扫描入口
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from scanner import scan, print_results, export_results

# ===== 在这里修改默认参数 =====
CONFIG = {
    # 通用参数
    'strategy': 'vr_slope',          # 策略: vp_sync / vp_pulse / vr_slope
    'file': 'codes.txt',             # 股票代码文件
    'date': '20260521',                    # 日期 YYYYMMDD，None=今天
    'n': 5,                          # 过去n个交易日
    'until': None,                   # 截至时间 HH:MM，None=全天
    'no_filter': False,              # True=不过滤创业板/科创板/北交所
    'change_min': -100,              # 涨幅下限(%)
    'change_max': 100,               # 涨幅上限(%)
    'csv': False,                    # True=导出CSV

    # vr_slope 策略参数
    'vr_slope_window': 4,            # 窗口大小（分钟）
    'vr_slope': 4,                   # 量比斜率角度阈值（度）
    'vr_up': True,                   # 窗口首尾量比是否增加
    'vr_slope_price_up': True,       # 窗口首尾价格是否不跌
    'vr_slope_min_hits': 1,          # 最少命中窗口数
    'vr_slope_merge_gap': 2,         # 命中窗口合并间隔

    # vp_pulse 策略参数
    'pulse': 2.0,                    # 脉冲倍数阈值
    'min_hits': 3,                   # 最少脉冲点数
    'pulse_price_up': True,          # 脉冲点是否要求价格上涨
    'vol_up': True,                  # 脉冲点是否要求量比递增
    'pulse_merge_gap': 2,            # 脉冲点合并间隔

    # vp_sync 策略参数
    'window': 5,                     # 滑动窗口大小（分钟）
    'sync_threshold': 0.25,          # 同步率阈值
    'vr_threshold': 0.8,             # 量比阈值
}
# ================================


def main():
    cfg = CONFIG.copy()

    # 命令行覆盖（简单解析）
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        key = args[i].lstrip('-')
        if i + 1 < len(args) and not args[i + 1].startswith('--'):
            val = args[i + 1]
            # 尝试转数字
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            cfg[key] = val
            i += 2
        else:
            cfg[key] = True
            i += 1

    # 日期（确保是字符串）
    date = str(cfg['date']) if cfg['date'] else datetime.now().strftime('%Y%m%d')

    # 截至时间
    until_hour = None
    until_minute = None
    if cfg['until']:
        parts = str(cfg['until']).split(':')
        until_hour = int(parts[0])
        until_minute = int(parts[1])

    # 读取股票列表
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['file'])
    if not os.path.exists(file_path):
        print("文件不存在: %s" % file_path)
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        codes = [line.strip() for line in f if line.strip()]

    if not codes:
        print("股票列表为空")
        sys.exit(1)

    # 过滤创业板/科创板/北交所
    if not cfg.get('no_filter', False):
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
    strategy = cfg['strategy']
    if strategy == 'vr_slope':
        strategy_kwargs = {
            'window': cfg['vr_slope_window'],
            'vr_slope': cfg['vr_slope'],
            'vr_up': cfg['vr_up'],
            'price_up': cfg['vr_slope_price_up'],
            'min_hits': cfg['vr_slope_min_hits'],
            'merge_gap': cfg['vr_slope_merge_gap'],
        }
        print("策略: %s  日期: %s  股票数: %d  窗口: %d分钟  量比斜率: %.0f度  量比增加: %s  价格上涨: %s  最少命中: %d  合并间隔: %d%s" % (
            strategy, date, len(codes), cfg['vr_slope_window'], cfg['vr_slope'], cfg['vr_up'],
            cfg['vr_slope_price_up'], cfg['vr_slope_min_hits'], cfg['vr_slope_merge_gap'],
            "  截至时间: %s" % cfg['until'] if cfg['until'] else ""))
    elif strategy == 'vp_pulse':
        strategy_kwargs = {
            'pulse': cfg['pulse'],
            'min_hits': cfg['min_hits'],
            'price_up': cfg['pulse_price_up'],
            'vol_up': cfg['vol_up'],
            'merge_gap': cfg['pulse_merge_gap'],
        }
        print("策略: %s  日期: %s  股票数: %d  脉冲阈值: %.1f  最少脉冲点: %d  价格上涨: %s  量比递增: %s  合并间隔: %d%s" % (
            strategy, date, len(codes), cfg['pulse'], cfg['min_hits'], cfg['pulse_price_up'],
            cfg['vol_up'], cfg['pulse_merge_gap'],
            "  截至时间: %s" % cfg['until'] if cfg['until'] else ""))
    elif strategy == 'vp_sync':
        strategy_kwargs = {
            'window': cfg['window'],
            'sync_threshold': cfg['sync_threshold'],
            'vr_threshold': cfg['vr_threshold'],
        }
        print("策略: %s  日期: %s  股票数: %d  窗口: %d分钟  同步阈值: %.2f  量比阈值: %.1f%s" % (
            strategy, date, len(codes), cfg['window'], cfg['sync_threshold'], cfg['vr_threshold'],
            "  截至时间: %s" % cfg['until'] if cfg['until'] else ""))
    else:
        strategy_kwargs = {}

    # 扫描
    results = scan(codes, date, strategy, cfg['n'],
                   until_hour=until_hour, until_minute=until_minute,
                   change_min=cfg['change_min'], change_max=cfg['change_max'],
                   **strategy_kwargs)

    # 输出
    print_results(results, strategy, date)

    # 导出
    if cfg.get('csv', False):
        export_results(results, strategy, date)


if __name__ == "__main__":
    main()
