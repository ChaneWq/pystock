from day_index import init_create_client
import pandas as pd

client = init_create_client()
code = '000400'
df = client.bars(symbol=code, frequency=7, offset=1600)

# 过滤早上10:00及之前的数据
# 假设hour和minute字段是整数类型
df_filtered = df[(df['hour'] < 10) | ((df['hour'] == 10) & (df['minute'] <= 0))]

# 重命名字段
df_renamed = df_filtered.rename(columns={
    'vol': 'vol',  # 保持不变
    'amount': 'amout',  # 修正拼写
    'year': 'trade_date',  # 假设用年作为交易日期
    'volume': 'volume'
})

# 选择需要的字段并重新排列
# 注意：原始数据中没有单独的low字段，假设是low字段
df_final = df_renamed[['open', 'close', 'high', 'low', 'vol', 'amout', 'trade_date', 'hour', 'minute', 'volume']]

# 保存为CSV
df_final.to_csv('000400_filtered.csv', index=False)