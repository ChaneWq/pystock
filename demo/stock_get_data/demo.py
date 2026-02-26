import requests
import json
from mootdx.quotes import Quotes
import pandas as pd
# import stock.tdx_indicator as tdx_indicator
import tdx_indicator as tdx_indicator

def init_create_client():
    """
    初始化client，用于传入后续的方法
    """
    client = Quotes.factory(market='std')
    return client
client = init_create_client()
code = '600702'

df = client.bars(symbol=code, frequency='day', offset=1000)
custom_index = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
# 使用自定义的整数索引列作为索引
df.set_index(custom_index, inplace=True)

print(df.columns)
# Index(['open', 'close', 'high', 'low', 'vol', 'amount', 'year', 'month', 'day',
#        'hour', 'minute', 'datetime', 'volume'],
#       dtype='object')
print(df)

# 计算涨幅字段（百分比）
df['price_change_rate'] = (df['close'] - df['close'].shift(1)) / df['close'].shift(1) * 100

# 将涨幅保留两位小数
df['price_change_rate'] = df['price_change_rate'].round(2)

# 显示结果
# print(df[['close', '涨幅','year','month','day']].head(-10))
print(df[['close', 'price_change_rate','year','month','day']])


df.to_csv('test.csv',index=False)