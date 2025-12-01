import pandas as pd
import numpy as np
import pymysql
from sqlalchemy import create_engine
from mootdx.quotes import Quotes
import tdx_indicator as tdx_indicator

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time


# ---------------- MySQL 写入 ---------------- #

def df_to_mysql(df, table_name="stock_features",
                mysql_host="localhost",
                mysql_user="root",
                mysql_password="root",
                mysql_db="stock",
                port=3306):

    engine = create_engine(
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{port}/{mysql_db}?charset=utf8mb4"
    )

    dtype_mapping = {
        'int64': 'BIGINT',
        'float64': 'DOUBLE',
        'object': 'TEXT',
        'datetime64[ns]': 'DATETIME',
        'bool': 'TINYINT',
    }

    # 建表执行一次
    if not hasattr(df_to_mysql, "table_created"):
        lock = threading.Lock()
        with lock:
            if not hasattr(df_to_mysql, "table_created"):

                create_sql = """
                    CREATE TABLE IF NOT EXISTS stock_features (
                        code VARCHAR(10) NOT NULL,
                        trade_date DATE NOT NULL,
                """

                for col in df.columns:
                    if col in ("code", "trade_date"):
                        continue
                    col_type = str(df[col].dtype)
                    mysql_type = dtype_mapping.get(col_type, 'TEXT')
                    create_sql += f"`{col}` {mysql_type},\n"

                create_sql += "PRIMARY KEY (`code`, `trade_date`));"

                conn = pymysql.connect(
                    host=mysql_host, user=mysql_user, password=mysql_password,
                    database=mysql_db, charset="utf8mb4"
                )
                cursor = conn.cursor()
                cursor.execute(create_sql)
                conn.commit()
                cursor.close()
                conn.close()

                df_to_mysql.table_created = True

    df = df.where(pd.notnull(df), None)
    df.to_sql(table_name, engine, if_exists="append", index=False)


# ---------------- 指标函数 ---------------- #

def ZX_short_term_trend(close):
    ema1 = tdx_indicator.EMA(close, 10)
    return tdx_indicator.EMA(ema1, 10)


def ZX_bull_bear_line(close, M1=14, M2=28, M3=57, M4=114):
    ma1 = tdx_indicator.MA(close, M1)
    ma2 = tdx_indicator.MA(close, M2)
    ma3 = tdx_indicator.MA(close, M3)
    ma4 = tdx_indicator.MA(close, M4)
    return (ma1 + ma2 + ma3 + ma4) / 4


# ---------------- 单支股票逻辑：不再创建 client ---------------- #

def save_stock_features(code, client, offset=400):
    """
    单支股票任务（client 由线程创建，不再每个code创建）
    """
    try:
        df = client.bars(symbol=code, frequency="day", offset=offset)
        df.index = pd.RangeIndex(1, len(df) + 1)

        close, high, low = df["close"], df["high"], df["low"]

        # --- 指标 ---
        K, D, J = tdx_indicator.KDJ(close, high, low)
        BBI = tdx_indicator.BBI(close)
        DIF, DEA, MACD = tdx_indicator.MACD(close)

        zx_trend = ZX_short_term_trend(close)
        zx_bull = ZX_bull_bear_line(close)

        df["K"], df["D"], df["J"] = np.round(K, 2), np.round(D, 2), np.round(J, 2)
        df["BBI"] = np.round(BBI, 2)

        for n in [5, 7, 10, 20, 30, 40, 45, 60, 90, 250]:
            df[f"MA{n}"] = np.round(tdx_indicator.MA(close, n), 2)

        df["DIF"], df["DEA"], df["MACD"] = np.round(DIF, 2), np.round(DEA, 2), np.round(MACD, 2)

        df["zx_short_term_trend"] = np.round(zx_trend, 2)
        df["zx_bull_bear_line"] = np.round(zx_bull, 2)

        df["trade_date"] = pd.to_datetime(df[["year", "month", "day"]])
        df["code"] = code

        df = df[
            ["code", "trade_date", "open", "close", "high", "low", "vol", "amount",
             "zx_short_term_trend", "zx_bull_bear_line",
             "K", "D", "J", "BBI",
             "MA5", "MA7", "MA10", "MA20", "MA30", "MA40", "MA45", "MA60", "MA90", "MA250",
             "DIF", "DEA", "MACD"]
        ]

        df_to_mysql(df)
        return (code, "OK")

    except Exception as e:
        return (code, f"ERROR: {e}")


# ---------------- 获取全部股票代码 ---------------- #

def get_all_codes():
    conn = pymysql.connect(host="localhost", user="root", password="root",
                           database="stock", charset="utf8mb4")
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM stock_name2;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r[0] for r in rows]


# ---------------- 每个线程只创建一个 client ---------------- #

def worker(codes, offset):
    """
    单线程：创建一个 client 后处理多个 code
    """
    client = Quotes.factory(market="std")   # 线程只创建一次
    print('*'*100)
    results = []
    for code in codes:
        results.append(save_stock_features(code, client, offset))
    return results


# ---------------- 多线程执行 ---------------- #

def run_all_codes(offset=400, max_workers=5):
    codes = get_all_codes()
    print(codes)
    print(f"✔ 共 {len(codes)} 个股票，启动 {max_workers} 线程")

    # 分割 codes 到每个线程
    chunk = (len(codes) + max_workers - 1) // max_workers
    code_groups = [codes[i:i + chunk] for i in range(0, len(codes), chunk)]

    success, fail = [], []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(worker, group, offset): group for group in code_groups
        }

        for future in as_completed(futures):
            results = future.result()
            for code, msg in results:
                if msg == "OK":
                    print(f"✔ {code} 完成")
                    success.append(code)
                else:
                    print(f"❌ {code} 失败：{msg}")
                    fail.append(code)

    print("\n========== 运行完成 ==========")
    print("成功：", len(success))
    print("失败：", len(fail))
    if fail:
        print("失败股票：", fail)


# ---------------- 运行 ---------------- #

run_all_codes(offset=1800, max_workers=5)
# codes = get_all_codes()
# print(codes)
