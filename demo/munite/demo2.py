from day_index import init_create_client
import pandas as pd

client = init_create_client()
code = '000400'
date = '20260420'
# date = '20150120'
# df = client.minutes(symbol=code,date='20230705')
df = client.minutes(symbol=code,date=date)

# 添加 hour 和 minute 字段
# A 股交易时间：9:30-11:30, 13:00-15:00
# 上午 120 分钟 (0-119), 下午 120 分钟 (120-239)
def get_trade_hour_minute(index):
    """根据索引计算交易小时和分钟"""
    if index < 120:  # 上午 9:30-11:30
        hour = 9
        minute = 30 + index
        if minute >= 60:
            hour += 1
            minute -= 60
    else:  # 下午 13:00-15:00
        afternoon_index = index - 120
        hour = 13
        minute = afternoon_index
        if minute >= 60:
            hour += 1
            minute -= 60
    
    return hour, minute

# 添加 hour 和 minute 列
hours = []
minutes = []
for i in range(len(df)):
    h, m = get_trade_hour_minute(i)
    hours.append(h)
    minutes.append(m)

df['hour'] = hours
df['minute'] = minutes

# 添加 code 字段
df['code'] = code

# 添加 trade_date 字段，将 date 转换为 2026-03-06 格式
from datetime import datetime
trade_date = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
df['trade_date'] = trade_date

print(df)

