import pandas as pd
import mysql.connector
from sqlalchemy import create_engine


def csv_to_mysql_general(csv_file, table_name):
	"""
	通用版本的CSV导入MySQL，自动识别所有字段

	参数:
	csv_file: CSV文件路径
	table_name: 要创建的MySQL表名
	"""
	
	try:
		# 1. 读取CSV文件
		print("正在读取CSV文件...")
		# df = pd.read_csv(csv_file)
		# df = pd.read_csv(csv_file, sep='\t')
		df = pd.read_csv(csv_file, sep=',')
		print(f"成功读取CSV文件，共 {len(df)} 行数据，{len(df.columns)} 个字段")
		
		# 显示字段信息
		print("字段列表:")
		for i, col in enumerate(df.columns):
			print(f"  {i + 1}. {col} (类型: {df[col].dtype})")
		
		# 2. 连接到数据库
		print("正在连接数据库...")
		conn = mysql.connector.connect(
			host='10.1.3.40',
			port=9030,
			user='gzqp_bigdata_prod',
			password='bg3c1jqy_FGX.m5#mdz',
			database='gzqp_bigdata_dev'
		)
		cursor = conn.cursor()
		
		# 3. 分析字段类型并生成创建表的SQL
		column_definitions = []
		for col in df.columns:
			# 根据数据类型选择合适的数据库字段类型
			dtype = str(df[col].dtype)
			
			if dtype.startswith('int'):
				column_def = f"`{col}` INT"
			elif dtype.startswith('float'):
				column_def = f"`{col}` DECIMAL(20, 6)"
			elif dtype.startswith('datetime'):
				column_def = f"`{col}` DATETIME"
			else:
				# 对于字符串类型，计算最大长度
				max_length = df[col].astype(str).map(len).max()
				varchar_length = max(50, min(max_length + 200, 500))  # 限制在500以内
				column_def = f"`{col}` VARCHAR({varchar_length})"
			
			column_definitions.append(column_def)
		
		# 4. 创建表
		create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    "
		create_table_sql += ",\n    ".join(column_definitions)
		create_table_sql += "\n)"
		
		print(f"创建表SQL:\n{create_table_sql}")
		
		cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
		cursor.execute(create_table_sql)
		conn.commit()
		print(f"表 {table_name} 创建成功")
		
		# 5. 准备插入数据的SQL
		placeholders = ", ".join(["%s"] * len(df.columns))
		columns_str = ", ".join([f"`{col}`" for col in df.columns])
		insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
		
		# 6. 分批插入数据
		print("正在导入数据...")
		batch_size = 1000
		total_rows = len(df)
		
		# 将DataFrame转换为适合插入的格式
		data_to_insert = []
		for _, row in df.iterrows():
			# 处理NaN值为None（MySQL的NULL）
			row_values = [None if pd.isna(value) else value for value in row]
			data_to_insert.append(tuple(row_values))
		
		for i in range(0, total_rows, batch_size):
			batch = data_to_insert[i:i + batch_size]
			cursor.executemany(insert_sql, batch)
			conn.commit()
			
			progress = min(i + batch_size, total_rows)
			print(f"已导入 {progress}/{total_rows} 行数据 ({progress / total_rows * 100:.1f}%)")
		
		# 7. 验证数据
		cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
		count = cursor.fetchone()[0]
		print(f"验证: 表中实际有 {count} 条记录")
		
		# 显示表结构
		cursor.execute(f"DESCRIBE {table_name}")
		print("\n表结构:")
		for col_info in cursor.fetchall():
			print(f"  {col_info[0]}: {col_info[1]}")
		
		# 关闭连接
		cursor.close()
		conn.close()
		print("数据导入完成！")
	
	except Exception as e:
		print(f"发生错误: {e}")
		import traceback
		traceback.print_exc()


def preview_csv_structure(csv_file):
	"""
	预览CSV文件结构
	"""
	try:
		# df = pd.read_csv(csv_file)
		df = pd.read_csv(csv_file,sep='\t')
		print(df)
		print(f"文件: {csv_file}")
		print(f"行数: {len(df)}, 列数: {len(df.columns)}")
		print("\n字段详细信息:")
		for col in df.columns:
			dtype = df[col].dtype
			sample_value = df[col].iloc[0] if len(df) > 0 else "N/A"
			unique_count = df[col].nunique()
			print(f"  {col}: {dtype} (示例: {sample_value}, 唯一值: {unique_count})")
		
		print(f"\n前5行数据:")
		print(df.head())
		
	except Exception as e:
		print(f"预览错误: {e}")


# 使用示例
if __name__ == "__main__":
	# csv_file_path = 'your_file.csv'  # 替换为你的CSV文件路径
	# mysql_table_name = 'your_table'  # 替换为你想要的表名
	
	csv_file_path = r'D:\wu\pystock\demo\stock_get_data\test.csv'  # 替换为你的CSV文件路径
	mysql_table_name = 'tmp_sto'  # 替换为你想要的表名
	
	# 先预览文件结构
	print("=== CSV文件预览 ===")
	preview_csv_structure(csv_file_path)
	
	print("\n=== 开始导入数据 ===")
	csv_to_mysql_general(csv_file_path, mysql_table_name)