import pandas as pd
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from mootdx.quotes import Quotes
import tdx_indicator as tdx_indicator
from sqlalchemy import create_engine
import pymysql


# ----------------【通用 MySQL 写入函数】---------------- #

def df_to_mysql(df, table_name="stock_features",
                mysql_host="localhost",
                mysql_user="root",
                mysql_password="root",
                mysql_db="stock",
                port=3306):
    """
    通用 df 写入 MySQL（自动建表 + 自动类型转换 + 自动防重）
    """

    # 1. SQLAlchemy engine
    engine = create_engine(
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{port}/{mysql_db}?charset=utf8mb4"
    )

    # 2. dtype 映射
    dtype_mapping = {
        'int64': 'BIGINT',
        'float64': 'DOUBLE',
        'object': 'TEXT',
        'datetime64[ns]': 'DATETIME',
        'bool': 'TINYINT',
    }

    # ---------------- 建表 SQL ---------------- #
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            `code` VARCHAR(10) NOT NULL,
            `trade_date` DATE NOT NULL,
    """

    for col in df.columns:
        if col in ["code", "trade_date"]:
            continue
        col_type = str(df[col].dtype)
        mysql_type = dtype_mapping.get(col_type, 'TEXT')

        create_sql += f"`{col}` {mysql_type},\n"

    # 主键（避免重复插入）
    create_sql += "PRIMARY KEY (`code`, `trade_date`));"

    # 执行建表
    conn = pymysql.connect(
        host=mysql_host, user=mysql_user, password=mysql_password,
        database=mysql_db, charset="utf8mb4"
    )
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()
    cursor.close()
    conn.close()

    # 3. NaN → None（避免 mysql 错误）
    df = df.where(pd.notnull(df), None)

    # 4. 写入
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"✔ 写入 MySQL 成功 → {table_name}")


# ----------------【指标功能函数】---------------- #

def ZX_short_term_trend(close):
    ema1 = tdx_indicator.EMA(close, 10)
    return tdx_indicator.EMA(ema1, 10)


def ZX_bull_bear_line(close, M1=14, M2=28, M3=57, M4=114):
    ma1 = tdx_indicator.MA(close, M1)
    ma2 = tdx_indicator.MA(close, M2)
    ma3 = tdx_indicator.MA(close, M3)
    ma4 = tdx_indicator.MA(close, M4)
    return (ma1 + ma2 + ma3 + ma4) / 4.0


# ----------------【最终通用封装函数】---------------- #

def save_stock_features(code,client, offset=400):


    # 获取 K 线
    df = client.bars(symbol=code, frequency="day", offset=offset)
    df.index = pd.RangeIndex(1, len(df) + 1)

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # 指标计算
    K, D, J = tdx_indicator.KDJ(close, high, low)
    BBI = tdx_indicator.BBI(close)

    ma = lambda n: tdx_indicator.MA(close, n)

    DIF, DEA, MACD = tdx_indicator.MACD(close)

    zx_trend = ZX_short_term_trend(close)
    zx_bull = ZX_bull_bear_line(close)

    # 加入 df
    df["K"] = np.round(K, 2)
    df["D"] = np.round(D, 2)
    df["J"] = np.round(J, 2)
    df["BBI"] = np.round(BBI, 2)

    for n in [5, 7, 10, 20, 30, 40, 45, 60, 90, 250]:
        df[f"MA{n}"] = np.round(ma(n), 2)

    df["DIF"] = np.round(DIF, 2)
    df["DEA"] = np.round(DEA, 2)
    df["MACD"] = np.round(MACD, 2)

    df["zx_short_term_trend"] = np.round(zx_trend, 2)
    df["zx_bull_bear_line"] = np.round(zx_bull, 2)

    df["trade_date"] = pd.to_datetime(df[["year", "month", "day"]])
    df["code"] = code

    # 选择需要的列
    columns = [
        "code", "trade_date", "open", "close", "high", "low", "vol", "amount",
        "zx_short_term_trend", "zx_bull_bear_line",
        "K", "D", "J", "BBI",
        "MA5", "MA7", "MA10", "MA20", "MA30", "MA40", "MA45", "MA60", "MA90", "MA250",
        "DIF", "DEA", "MACD"
    ]
    df = df[columns]

    # 写入 MySQL
    df_to_mysql(df, table_name="stock_features")



# ---------------- 获取全部 code ---------------- #

def get_all_codes(mysql_host="localhost",
                  mysql_user="root",
                  mysql_password="root",
                  mysql_db="stock",
                  port=3306):
    """
    从 stock_name 表读取所有股票 code
    """
    conn = pymysql.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM stock_name;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    codes = [r[0] for r in rows]
    print(f"✔ 获取到股票数量：{len(codes)} 个")
    return codes


# ---------------- 批量运行 ---------------- #
import time
def run_all_codes(offset=400, table_name="stock_features"):
    """
    自动遍历 stock_name 表里的所有 code 并执行 save_stock_features
    """
    codes = get_all_codes()
    print(codes)

    success = 0
    fail = []
    client = Quotes.factory(market="std")

    for idx, code in enumerate(codes):
        print(f"\n=== ({idx + 1}/{len(codes)}) 正在处理 {code} ===")

        try:
            save_stock_features(code=code,client=client, offset=offset)
            success += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ 处理 {code} 出错：{e}")
            break
            fail.append(code)

    print("\n================= 批量处理完成 =================")
    print(f"成功：{success} 个")
    print(f"失败：{len(fail)} 个")

    if fail:
        print("失败的股票代码：", fail)


run_all_codes(offset=1800)
