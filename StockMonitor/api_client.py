# api_client.py

import pandas as pd

def get_cur_data(code: str, client=""):
    """
    获取指定股票的最新数据和前一日数据。
    返回 (current_data, previous_data) 两个 pandas.Series：
      current_data 包含 open, close, high, low, vol, amount 等；
      previous_data 包含 prev_open, prev_close, prev_high, prev_low, prev_vol, prev_amount 等。
    使用示例：
        cur_data, prev_data = get_cur_data('000400', client)
        latest_close = cur_data['close']
        previous_close = prev_data['prev_close']
    """
    # 以下为示例实现，需按你实际数据接口调整：
    df = client.bars(symbol=code, frequency='day', offset=2)
    if df is not None and len(df) >= 2:
        current_data = df.iloc[-1]
        previous_data = df.iloc[-2].add_prefix('prev_')
        return current_data, previous_data
    elif df is not None and len(df) == 1:
        current_data = df.iloc[-1]
        previous_data = pd.Series(dtype='object')
        return current_data, previous_data
    else:
        return pd.Series(dtype='object'), pd.Series(dtype='object')
