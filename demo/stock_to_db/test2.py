import pandas as pd
from sqlalchemy import create_engine
import pymysql

def df_to_mysql(df, table_name="stock_features",
                mysql_host="localhost",
                mysql_user="root",
                mysql_password="root",
                mysql_db="stocks",
                port=3306):

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
    conn = pymysql.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()
    cursor.close()
    conn.close()

    # 4. 将 df append 写入 MySQL
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"DataFrame 已成功写入 MySQL 表：{table_name}")

