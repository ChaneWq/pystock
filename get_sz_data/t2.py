import requests
import csv
import json
import re
from typing import Dict, Any, Optional
"""
上证指数数据下载（指定日期范围）日，周，月k数据
来源url: https://q.stock.sohu.com/zs/000001/lshq.shtml
"""

def requests_fetch_data(url: str, params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> str:
	"""
	获取股票数据的封装函数

	Args:
		url: 请求的URL地址
		params: 请求参数字典
		headers: 请求头字典，默认为常见的浏览器请求头

	Returns:
		str: 响应文本内容
	"""
	# 默认请求头
	default_headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
		'Accept': 'application/json'
	}
	
	# 合并请求头
	if headers:
		final_headers = {**default_headers, **headers}
	else:
		final_headers = default_headers
	
	try:
		# 发送GET请求
		response = requests.get(url, params=params, headers=final_headers)
		response.raise_for_status()  # 检查请求是否成功
		
		return response.text
	
	except requests.exceptions.RequestException as e:
		print(f"请求失败: {e}")
		return ""


def parse_stock_data(response_text: str) -> Dict[str, Any]:
	"""
	解析股票数据响应文本
	"""
	# 使用正则表达式提取JSON数据部分
	match = re.search(r'historySearchHandler\((.*?)\);?$', response_text)
	if not match:
		raise ValueError("无法解析响应数据格式")
	
	json_data = match.group(1)
	data = json.loads(json_data)[0]  # 响应数据是一个包含单个字典的列表
	
	return data


def save_stock_data_to_csv(data: Dict[str, Any], filename: str = "stock_data.csv"):
	"""
	将股票数据保存为CSV文件
	"""
	# CSV表头
	headers = ["日期", "开盘价", "收盘价", "涨跌额", "涨跌幅", "最低价", "最高价", "成交量", "成交金额(万)", "换手率"]
	
	with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
		writer = csv.writer(csvfile)
		
		# 写入表头
		writer.writerow(headers)
		
		# 写入数据
		for row in data['hq']:
			writer.writerow(row)
	
	print(f"数据已保存到 {filename}")


# 使用示例
if __name__ == "__main__":

	base_url = 'https://q.stock.sohu.com/hisHq'
	"""
	period:
		d:天
		w:周
		m:月
	"""
	params = {
		'code': 'zs_000001',
		'start':'20250108',
		'end':'20250115',
		'stat': 1,
		'order': 'D',
		'period': 'd',
		'callback': 'historySearchHandler',
		'rt': 'jsonp'
	}

	result = requests_fetch_data(base_url, params=params)
	print(result)
	
	if result:
		try:
			# 解析数据
			stock_data = parse_stock_data(result)
			print("解析后的数据:")
			print(f"股票代码: {stock_data['code']}")
			print(f"状态: {stock_data['status']}")
			print(f"数据条数: {len(stock_data['hq'])}")
			print("\n前3条数据示例:")
			for i, row in enumerate(stock_data['hq'][:3]):
				print(f"{i + 1}. {row}")
			
			print("\n" + "=" * 60 + "\n")
			
			# 保存为简单CSV（只包含价格数据）
			save_stock_data_to_csv(stock_data, "stock_simple.csv")
		
		except (ValueError, KeyError, json.JSONDecodeError) as e:
			print(f"数据处理错误: {e}")
	else:
		print("未能获取到数据")