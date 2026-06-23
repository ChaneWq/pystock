# minute_vr_fetcher.py - 分时量比数据获取层
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from day_index import init_create_client
import pandas as pd
from datetime import datetime


def get_minute_data(code, date, client):
    """
    获取指定股票指定日期的分时数据

    参数:
        code: 股票代码，如 '000400'
        date: 日期字符串，如 '20260420'
        client: 通达信客户端

    返回:
        DataFrame，包含 open, close, high, low, vol, hour, minute, trade_date
    """
    df = client.minutes(symbol=code, date=date)
    if df is None or df.empty:
        print(f"[Fetcher] 未获取到 {code} 在 {date} 的分时数据")
        return pd.DataFrame()

    # 补全 hour, minute 字段
    hours = []
    minutes = []
    for i in range(len(df)):
        h, m = _get_trade_hour_minute(i)
        hours.append(h)
        minutes.append(m)

    df['hour'] = hours
    df['minute'] = minutes

    # 补全 trade_date
    trade_date = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
    df['trade_date'] = trade_date

    return df


def get_prev_n_day_vol(code, n=5, client=None, date=None):
    """
    获取指定股票过去n个交易日的日线成交量及昨收价

    获取足够多的日线数据，根据目标日期定位：
      vol_list = 目标日期前 n 日成交量（用于计算分钟均量）
      prev_close = 目标日期前一交易日的收盘价（即昨收价）

    参数:
        code: 股票代码
        n: 交易日天数，默认5
        client: 通达信客户端
        date: 目标日期，如 '20260514'，None则取最新

    返回:
        dict: {'vol_list': list, 'prev_close': float}
            vol_list: 过去n个交易日的成交量列表
            prev_close: 昨收价（目标日期前一交易日收盘价）
    """
    # 多取一些数据确保能覆盖目标日期
    offset = n + 50 if date else n + 1
    df = client.bars(symbol=code, frequency='day', offset=offset)
    if df is None or df.empty:
        print(f"[Fetcher] 未获取到 {code} 的日线数据")
        return None

    if date:
        # 根据目标日期定位（只比较日期部分，忽略时间）
        target_date = pd.to_datetime(date, format='%Y%m%d').date()
        df['dt_parsed'] = pd.to_datetime(df['datetime']).dt.date
        mask = df['dt_parsed'] <= target_date
        if not mask.any():
            print(f"[Fetcher] 日线数据不包含 {date} 之前的数据")
            return None
        target_idx = df[mask].index[-1]
        # 取目标日期及之前 n+1 行
        loc = df.index.get_loc(target_idx)
        if loc < n:
            print(f"[Fetcher] {code} 在 {date} 之前数据不足 {n} 日")
            return None
        rows = df.iloc[loc - n:loc + 1]
        vol_list = rows['vol'].tolist()[:n]
        prev_close = float(rows['close'].iloc[n - 1])
    else:
        rows = df.iloc[-(n + 1):]
        vol_list = rows['vol'].tolist()[:n]
        prev_close = float(rows['close'].iloc[n - 1])

    return {'vol_list': vol_list, 'prev_close': prev_close}


def _get_trade_hour_minute(index):
    """
    根据分时数据索引计算交易小时和分钟

    A股交易时间：9:30-11:30, 13:00-15:00
    上午 120 分钟 (0-119), 下午 120 分钟 (120-239)
    """
    if index < 120:  # 上午 9:30-11:30
        total_minutes = 9 * 60 + 30 + index  # 从9:00开始偏移30分钟
        hour = total_minutes // 60
        minute = total_minutes % 60
    else:  # 下午 13:00-15:00
        total_minutes = 13 * 60 + (index - 120)
        hour = total_minutes // 60
        minute = total_minutes % 60
    return hour, minute