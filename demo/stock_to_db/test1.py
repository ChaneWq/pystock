import requests
import mysql.connector
import json
from mootdx.quotes import Quotes
import pandas as pd
import numpy as np
import tdx_indicator as tdx_indicator

import pandas as pd
from sqlalchemy import create_engine
import pymysql

# def df_to_mysql(df, table_name="stock_features",
#                 mysql_host="localhost",
#                 mysql_user="root",
#                 mysql_password="root",
#                 mysql_db="stock",
#                 port=3306):
def df_to_mysql(df, table_name="stock_features1",
                mysql_host="10.1.3.40",
                mysql_user="gzqp_bigdata_prod",
                mysql_password="bg3c1jqy_FGX.m5#mdz",
                mysql_db="gzqp_bigdata_dev",
                port=9030):
    # 1. 创建连接引擎
    engine = create_engine(
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{port}/{mysql_db}?charset=utf8mb4"
    )

    # 2. 自动生成建表 SQL（通用）
    dtype_mapping = {
        'int64': 'BIGINT',
        'float64': 'DOUBLE',
        'object': 'TEXT',
        'datetime64[ns]': 'DATETIME',
        'bool': 'TINYINT'
    }

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
    """

    for col in df.columns:
        col_type = str(df[col].dtype)

        mysql_type = dtype_mapping.get(col_type, 'TEXT')
        if mysql_type == 'TEXT' and "datetime" in col_type:
            mysql_type = "DATETIME"

        create_sql += f"`{col}` {mysql_type},\n"

    create_sql = create_sql.rstrip(",\n") + ");"

    # 3. 连接 MySQL 创建表
    # conn = pymysql.connect(
    #     host=mysql_host,
    #     user=mysql_user,
    #     password=mysql_password,
    #     database=mysql_db,
    #     charset='utf8mb4'
    # )
    conn = mysql.connector.connect(
        host=mysql_host, user=mysql_user, password=mysql_password, port=port,
        database=mysql_db, charset="utf8mb4"
    )
    cursor = conn.cursor()
    # cursor.execute(create_sql)
    conn.commit()
    cursor.close()
    conn.close()

    # 4. 将 df append 写入 MySQL
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"DataFrame 已成功写入 MySQL 表：{table_name}")


def init_create_client():
    """
    初始化client，用于传入后续的方法
    """
    client = Quotes.factory(market='std')
    return client

def ZX_short_term_trend(close):
    """
    知行短期趋势线: EMA(EMA(C,10),10)
    """
    ema1 = tdx_indicator.EMA(close, 10)
    zx_short_term_trend = tdx_indicator.EMA(ema1, 10)
    return zx_short_term_trend

def ZX_bull_bear_line(close, M1=14, M2=28, M3=57, M4=114):
    """
    知行多空线: (MA(CLOSE,M1)+MA(CLOSE,M2)+MA(CLOSE,M3)+MA(CLOSE,M4))/4
    """
    ma1 = tdx_indicator.MA(close, M1)
    ma2 = tdx_indicator.MA(close, M2)
    ma3 = tdx_indicator.MA(close, M3)
    ma4 = tdx_indicator.MA(close, M4)

    zx_bull_bear_line = (ma1 + ma2 + ma3 + ma4) / 4.0
    return zx_bull_bear_line

code = '000400'
client = Quotes.factory(market='std')
# 生成自定义的整数索引列
df = client.bars(symbol=code, frequency='day', offset=100)  # 获取最近300日东方财富k线

df['a'] = pd.to_datetime(df[['year', 'month', 'day']])
b = df[(df['a']>'2026-01-08') & (df['a']<'2026-01-13')]
print(b)

custom_index = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
# 使用自定义的整数索引列作为索引
df.set_index(custom_index, inplace=True)
close = df['close']
high = df['high']
low = df['low']
K, D, J = tdx_indicator.KDJ(close, high, low)
BBI = tdx_indicator.BBI(close)
ma5 = tdx_indicator.MA(close,5)
ma7 = tdx_indicator.MA(close,7)
ma10 = tdx_indicator.MA(close,10)
ma25 = tdx_indicator.MA(close,250)
ma20 = tdx_indicator.MA(close,20)
ma30 = tdx_indicator.MA(close,30)
ma40 = tdx_indicator.MA(close,40)
ma45 = tdx_indicator.MA(close,45)
ma60 = tdx_indicator.MA(close,60)
ma90 = tdx_indicator.MA(close,90)
ma250 = tdx_indicator.MA(close,250)
DIF,DEA,MACD = tdx_indicator.MACD(close)
RSI1,RSI2,RSI3 = tdx_indicator.RSI(close)
hhv_high_4 = tdx_indicator.HHV(high, 4)
llv_low_4 = tdx_indicator.LLV(low, 4)
var1a = (hhv_high_4-close)/(hhv_high_4-llv_low_4)*100-90
var2a = tdx_indicator.SMA(var1a, 4,1)+100
var3a = (close-llv_low_4)/(hhv_high_4-llv_low_4)*100
var4a = tdx_indicator.SMA(var3a,6,1)
var5a = tdx_indicator.SMA(var4a,6,1)+100
var6a = var5a-var2a
# 砖型图
zxt = np.where(var6a > 4, var6a - 4, 0.0)

n1 = 3
n2 = 21
llv_low_n1 = tdx_indicator.LLV(low, n1)
llv_low_n2 = tdx_indicator.LLV(low, n2)
hhv_close_n1 = tdx_indicator.HHV(close, n1)
hhv_close_n2 = tdx_indicator.HHV(close, n2)
# 单针
dzs = (close-llv_low_n1)/(hhv_close_n1-llv_low_n1)*100
dzt = (close-llv_low_n2)/(hhv_close_n2-llv_low_n2)*100

# Calculate 知行短期趋势线
zx_trend = ZX_short_term_trend(close)

# Calculate 知行多空线 (using default parameters)
zx_bull_bear = ZX_bull_bear_line(close)

K = np.round(K, 2)
D = np.round(D, 2)
J = np.round(J, 2)
BBI = np.round(BBI, 2)
ma5 = np.round(ma5, 2)
ma7 = np.round(ma7, 2)
ma10 = np.round(ma10, 2)
ma20 = np.round(ma20, 2)
ma30 = np.round(ma30, 2)
ma40 = np.round(ma40, 2)
ma45 = np.round(ma45, 2)
ma60 = np.round(ma60, 2)
ma90 = np.round(ma90, 2)
ma250 = np.round(ma250, 2)
DIF = np.round(DIF, 2)
DEA = np.round(DEA, 2)
MACD = np.round(MACD, 2)
RSI1 = np.round(RSI1, 2)
RSI2 = np.round(RSI2, 2)
RSI3 = np.round(RSI3, 2)
zx_trend = np.round(zx_trend, 2)
zx_bull_bear = np.round(zx_bull_bear, 2)
zxt = np.round(zxt, 2)
dzs = np.round(dzs, 2)
dzt = np.round(dzt, 2)



# Add to dataframe
df['zx_short_term_trend'] = zx_trend
df['zx_bull_bear_line'] = zx_bull_bear


df['K'] = K
df['D'] = D
df['J'] = J
df['BBI'] = BBI
df['MA5'] = ma5
df['MA7'] = ma7
df['MA10'] = ma10
df['MA20'] = ma20
df['MA30'] = ma30
df['MA40'] = ma40
df['MA45'] = ma45
df['MA60'] = ma60
df['MA90'] = ma90
df['MA250'] = ma250
df['DIF'] = DIF
df['DEA'] = DEA
df['MACD'] = MACD
df['RSI1'] = RSI1
df['RSI2'] = RSI2
df['RSI3'] = RSI3
df['zxt'] = zxt
df['dzs'] = dzs
df['dzt'] = dzt
df['zx_short_term_trend'] = zx_trend
df['zx_bull_bear_line'] = zx_bull_bear
df['trade_date'] = pd.to_datetime(df[['year', 'month', 'day']])
df['code'] = code

print(df.columns)

df = df[['code','trade_date','open','close','high','low','vol','amount','zx_short_term_trend','zx_bull_bear_line','K','D','J','BBI','MA5','MA7','MA10','MA20','MA30','MA40','MA45','MA60','MA90','MA250','DIF','DEA','MACD','RSI1','RSI2','RSI3','zxt','dzs','dzt']]
print(df)
# df_to_mysql(df, table_name="stock_features1")