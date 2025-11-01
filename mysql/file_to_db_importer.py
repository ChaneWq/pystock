import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import os
"""
数据导入数据库脚本
支持csv，excel，自动识别文件类型
支持两种插入模式：1.创建并插入，2.只插入
"""

class FileToMySQL:
	"""
	文件导入MySQL工具类，支持CSV和Excel文件
	"""
	
	def __init__(self, db_config=None):
		"""
		初始化数据库配置

		参数:
		db_config: 数据库连接配置字典，包含host, port, user, password, database
		"""
		# 默认数据库配置
		self.default_db_config = {
			'host': '10.1.3.40',
			'port': 9030,
			'user': 'gzqp_bigdata_prod',
			'password': 'bg3c1jqy_FGX.m5#mdz',
			'database': 'gzqp_bigdata_dev'
		}
		
		# 如果提供了自定义配置，则使用自定义配置
		if db_config:
			self.default_db_config.update(db_config)
	
	def get_db_connection(self):
		"""获取数据库连接"""
		return mysql.connector.connect(**self.default_db_config)
	
	def file_to_mysql(self, file_path, table_name, mode='create_and_insert', **kwargs):
		"""
		文件数据导入MySQL，支持CSV和Excel文件

		参数:
		file_path: 文件路径（支持CSV和Excel）
		table_name: 要创建的MySQL表名
		mode: 导入模式，'create_and_insert'（先删表再创建）或 'insert_only'（只插入不删表）
		**kwargs: 其他参数，包括：
			- file_type: 文件类型，'auto'（自动检测）、'csv'或'excel'
			- sep: CSV文件分隔符，默认为逗号
			- encoding: 文件编码
			- sheet_name: Excel工作表名称（默认为第一个工作表）
			- batch_size: 批量插入大小，默认为1000
			- auto_add_columns: 是否自动添加缺失的列（仅insert_only模式有效）
		"""
		# 自动检测文件类型
		if kwargs.get('file_type', 'auto') == 'auto':
			file_type = self._detect_file_type(file_path)
		else:
			file_type = kwargs.get('file_type', 'csv')
		
		# 根据文件类型读取数据
		df = self._read_file(file_path, file_type, kwargs)
		
		if mode == 'create_and_insert':
			return self._file_to_mysql_create(df, file_path, table_name, file_type, kwargs)
		elif mode == 'insert_only':
			return self._file_to_mysql_insert(df, file_path, table_name, file_type, kwargs)
		else:
			raise ValueError(f"不支持的导入模式: {mode}，可选值: 'create_and_insert', 'insert_only'")
	
	def _detect_file_type(self, file_path):
		"""检测文件类型"""
		ext = os.path.splitext(file_path)[1].lower()
		if ext in ['.csv', '.txt']:
			return 'csv'
		elif ext in ['.xlsx', '.xls', '.xlsm']:
			return 'excel'
		else:
			raise ValueError(f"不支持的文件类型: {ext}，支持的类型: .csv, .xlsx, .xls")
	
	def _read_file(self, file_path, file_type, kwargs):
		"""读取文件内容为DataFrame"""
		try:
			if file_type == 'csv':
				read_params = {'filepath_or_buffer': file_path}
				if 'sep' in kwargs:
					read_params['sep'] = kwargs['sep']
				if 'encoding' in kwargs:
					read_params['encoding'] = kwargs['encoding']
				
				print(f"正在读取CSV文件: {file_path}")
				df = pd.read_csv(**read_params)
			
			elif file_type == 'excel':
				read_params = {'io': file_path}
				if 'sheet_name' in kwargs:
					read_params['sheet_name'] = kwargs['sheet_name']
				# 移除 encoding 参数，因为 read_excel 不需要这个参数
				
				print(f"正在读取Excel文件: {file_path}")
				df = pd.read_excel(**read_params)
			
			else:
				raise ValueError(f"不支持的文件类型: {file_type}")
			
			print(f"成功读取文件，共 {len(df)} 行数据，{len(df.columns)} 个字段")
			return df
		
		except Exception as e:
			print(f"读取文件错误: {e}")
			raise
	
	def _file_to_mysql_create(self, df, file_path, table_name, file_type, kwargs):
		"""
		创建表并插入数据模式（先删除原有表）
		"""
		try:
			# 显示字段信息
			print("字段列表:")
			for i, col in enumerate(df.columns):
				print(f"  {i + 1}. {col} (类型: {df[col].dtype})")
			
			# 连接到数据库
			print("正在连接数据库...")
			conn = self.get_db_connection()
			cursor = conn.cursor()
			
			# 分析字段类型并生成创建表的SQL
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
					varchar_length = max(50, min(max_length + 10, 500))
					column_def = f"`{col}` VARCHAR({varchar_length})"
				
				column_definitions.append(column_def)
			
			# 创建表
			create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    "
			create_table_sql += ",\n    ".join(column_definitions)
			create_table_sql += "\n)"
			
			print(f"创建表SQL:\n{create_table_sql}")
			
			cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
			cursor.execute(create_table_sql)
			conn.commit()
			print(f"表 {table_name} 创建成功")
			
			# 插入数据
			batch_size = kwargs.get('batch_size', 1000)
			self._insert_data(cursor, conn, df, table_name, batch_size)
			
			# 验证和显示结果
			self._verify_and_display(cursor, conn, table_name)
			
			print(f"{file_type.upper()}文件导入完成！")
		
		except Exception as e:
			print(f"发生错误: {e}")
			import traceback
			traceback.print_exc()
	
	def _file_to_mysql_insert(self, df, file_path, table_name, file_type, kwargs):
		"""
		只插入数据模式（不删除原有表）
		"""
		try:
			# 显示字段信息
			print("字段列表:")
			for i, col in enumerate(df.columns):
				print(f"  {i + 1}. {col} (类型: {df[col].dtype})")
			
			# 连接到数据库
			print("正在连接数据库...")
			conn = self.get_db_connection()
			cursor = conn.cursor()
			
			# 检查表是否存在，不存在则创建
			cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
			table_exists = cursor.fetchone() is not None
			
			if not table_exists:
				print(f"表 {table_name} 不存在，将创建新表")
				self._create_table_from_df(cursor, conn, df, table_name)
			else:
				print(f"表 {table_name} 已存在，将直接插入数据")
				
				# 检查表结构是否匹配
				cursor.execute(f"DESCRIBE {table_name}")
				existing_columns = [col[0] for col in cursor.fetchall()]
				
				# 检查CSV中的列是否都在表中存在
				missing_columns = set(df.columns) - set(existing_columns)
				if missing_columns:
					print(f"警告: 表中缺少以下列: {missing_columns}")
					if kwargs.get('auto_add_columns', False):
						print("正在自动添加缺失的列...")
						self._add_missing_columns(cursor, conn, df, table_name, missing_columns)
			
			# 插入数据
			batch_size = kwargs.get('batch_size', 1000)
			self._insert_data(cursor, conn, df, table_name, batch_size, check_columns=True)
			
			# 验证和显示结果
			self._verify_and_display(cursor, conn, table_name)
			
			print(f"{file_type.upper()}文件导入完成！")
		
		except Exception as e:
			print(f"发生错误: {e}")
			import traceback
			traceback.print_exc()
	
	def _create_table_from_df(self, cursor, conn, df, table_name):
		"""根据DataFrame创建表"""
		column_definitions = []
		for col in df.columns:
			dtype = str(df[col].dtype)
			
			if dtype.startswith('int'):
				column_def = f"`{col}` INT"
			elif dtype.startswith('float'):
				column_def = f"`{col}` DECIMAL(20, 6)"
			elif dtype.startswith('datetime'):
				column_def = f"`{col}` DATETIME"
			else:
				max_length = df[col].astype(str).map(len).max()
				varchar_length = max(50, min(max_length + 10, 500))
				column_def = f"`{col}` VARCHAR({varchar_length})"
			
			column_definitions.append(column_def)
		
		create_table_sql = f"CREATE TABLE {table_name} (\n    "
		create_table_sql += ",\n    ".join(column_definitions)
		create_table_sql += "\n)"
		
		print(f"创建表SQL:\n{create_table_sql}")
		cursor.execute(create_table_sql)
		conn.commit()
		print(f"表 {table_name} 创建成功")
	
	def _add_missing_columns(self, cursor, conn, df, table_name, missing_columns):
		"""添加缺失的列到已存在的表"""
		for col in missing_columns:
			dtype = str(df[col].dtype)
			
			if dtype.startswith('int'):
				alter_sql = f"ALTER TABLE {table_name} ADD COLUMN `{col}` INT"
			elif dtype.startswith('float'):
				alter_sql = f"ALTER TABLE {table_name} ADD COLUMN `{col}` DECIMAL(20, 6)"
			elif dtype.startswith('datetime'):
				alter_sql = f"ALTER TABLE {table_name} ADD COLUMN `{col}` DATETIME"
			else:
				max_length = df[col].astype(str).map(len).max()
				varchar_length = max(50, min(max_length + 10, 500))
				alter_sql = f"ALTER TABLE {table_name} ADD COLUMN `{col}` VARCHAR({varchar_length})"
			
			print(f"添加列: {alter_sql}")
			cursor.execute(alter_sql)
		
		conn.commit()
		print("缺失列添加完成")
	
	def _insert_data(self, cursor, conn, df, table_name, batch_size=1000, check_columns=False):
		"""插入数据到数据库"""
		if check_columns:
			# 只插入表中存在的列
			cursor.execute(f"DESCRIBE {table_name}")
			existing_columns = [col[0] for col in cursor.fetchall()]
			columns_to_insert = [col for col in df.columns if col in existing_columns]
		else:
			columns_to_insert = df.columns
		
		placeholders = ", ".join(["%s"] * len(columns_to_insert))
		columns_str = ", ".join([f"`{col}`" for col in columns_to_insert])
		insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
		
		print("正在导入数据...")
		total_rows = len(df)
		
		# 准备要插入的数据
		data_to_insert = []
		for _, row in df.iterrows():
			row_values = []
			for col in columns_to_insert:
				value = row[col]
				row_values.append(None if pd.isna(value) else value)
			data_to_insert.append(tuple(row_values))
		
		for i in range(0, total_rows, batch_size):
			batch = data_to_insert[i:i + batch_size]
			cursor.executemany(insert_sql, batch)
			conn.commit()
			
			progress = min(i + batch_size, total_rows)
			print(f"已导入 {progress}/{total_rows} 行数据 ({progress / total_rows * 100:.1f}%)")
	
	def _verify_and_display(self, cursor, conn, table_name):
		"""验证数据并显示表结构"""
		# 验证数据
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
	
	def preview_file_structure(self, file_path, **kwargs):
		"""
		预览文件结构，支持CSV和Excel

		参数:
		file_path: 文件路径
		**kwargs: 其他参数，如file_type, sep, encoding, sheet_name, nrows等
		"""
		try:
			# 自动检测文件类型
			file_type = kwargs.get('file_type', 'auto')
			if file_type == 'auto':
				file_type = self._detect_file_type(file_path)
			
			# 读取文件
			nrows = kwargs.get('nrows', 5)
			if file_type == 'csv':
				read_params = {'filepath_or_buffer': file_path}
				if 'sep' in kwargs:
					read_params['sep'] = kwargs['sep']
				if 'encoding' in kwargs:
					read_params['encoding'] = kwargs['encoding']
				read_params['nrows'] = nrows
				
				df = pd.read_csv(**read_params)
			
			elif file_type == 'excel':
				read_params = {'io': file_path}
				if 'sheet_name' in kwargs:
					read_params['sheet_name'] = kwargs['sheet_name']
				# 移除 encoding 参数，因为 read_excel 不需要这个参数
				read_params['nrows'] = nrows
				
				df = pd.read_excel(**read_params)
			
			print(f"文件: {file_path} (类型: {file_type})")
			print(f"行数: {len(df)}, 列数: {len(df.columns)}")
			print("\n字段详细信息:")
			for col in df.columns:
				dtype = df[col].dtype
				sample_value = df[col].iloc[0] if len(df) > 0 else "N/A"
				unique_count = df[col].nunique()
				print(f"  {col}: {dtype} (示例: {sample_value}, 唯一值: {unique_count})")
			
			print(f"\n前{nrows}行数据:")
			print(df.head(nrows))
		
		except Exception as e:
			print(f"预览错误: {e}")


# 使用示例
if __name__ == "__main__":
	# 数据库配置
	db_config = {
		'host': '10.1.3.40',
		'port': 9030,
		'user': 'gzqp_bigdata_prod',
		'password': 'bg3c1jqy_FGX.m5#mdz',
		'database': 'gzqp_bigdata_dev'
	}
	
	# 创建导入器实例
	importer = FileToMySQL(db_config)
	
	# csv_file_path = r'D:\对外文件\接收\2025-10-10\车型图\所有车型图生成的原图\0911文件车型图-make_model.csv'
	csv_file_path = r'D:\对外文件\接收\2025-10-29\策略数据入库\20251028三丰畅煜店铺新增关键词.xlsx'
	mysql_table_name = 'tmp_sku6'
	
	# 先预览文件结构
	importer.preview_file_structure(csv_file_path, sep=',', nrows=5)
	
	"""
	file_type:
		auto:自动识别
		csv,excel
	"""
	csv_params = {
		'file_type': 'auto',
		'sep': ',',
		'encoding': None,
		'batch_size': 1000
	}
	"""
	mode:
		create_and_insert
		insert_only
	"""
	importer.file_to_mysql(
		file_path=csv_file_path,
		table_name=mysql_table_name,
		mode='create_and_insert',
		**csv_params
	)
	