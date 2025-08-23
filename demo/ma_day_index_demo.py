import pandas as pd
import numpy as np
import requests
import json
from mootdx.quotes import Quotes
import pandas as pd
# import stock.tdx_indicator as tdx_indicator
import tdx_indicator as tdx_indicator
def MA(S, N):              # 求序列S的N日简单移动平均值，返回序列
    return pd.Series(S).rolling(N).mean().values
def init_create_client():
    client = Quotes.factory(market='std')
    return client
def get_day_ma(code,datestr="",client="",N=250):
    # client = Quotes.factory(market='std')
    # 生成自定义的整数索引列
    df = client.bars(symbol=code, frequency='day', offset=300)
    custom_index = pd.RangeIndex(start=1, stop=len(df)+1, step=1)
    # 使用自定义的整数索引列作为索引
    df.set_index(custom_index, inplace=True)
    try:
        close = df['close']
        ma = MA(close, N)
    except:
        # 如果是退市股票，直接返回0
        return (0,0,0)
    # K, D, J = tdx_indicator.KDJ(close, high, low)
    if(datestr==""):
        # print(J[-1])
        return ma[-1]
    else:
        try:
            index = df[df['datetime'].str.contains(datestr)].index-1
            # print(J[index])
            return ma[index][0]
        except:
            print("datestr格式不合规 或 该日期没有交易日 或 指定交易日错误")
            
if __name__ == '__main__':
	client = init_create_client()
	datestr = '2025-08-22'
	ma = get_day_ma('002544','',client,20)
	print(ma)