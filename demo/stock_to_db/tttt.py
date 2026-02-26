from sqlalchemy import create_engine
import pymysql
import pandas as pd

# ----------------【通用 MySQL 写入函数】---------------- #

def df_to_mysql(df, table_name="stock_features",
                mysql_host="10.1.3.40",
                mysql_user="gzqp_bigdata_prod",
                mysql_password="bg3c1jqy_FGX.m5#mdz",
                mysql_db="gzqp_bigdata_dev",
                port=9030):
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

df = '1'
df_to_mysql(df)