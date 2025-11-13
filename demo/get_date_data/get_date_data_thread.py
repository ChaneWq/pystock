import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime, timedelta
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

"""
获取日期数据，天干地支，阳历，农历
多线程
"""
def generate_date_range(start_date, end_date):
	"""生成日期范围内的所有日期"""
	start = datetime.strptime(start_date, "%Y-%m-%d")
	end = datetime.strptime(end_date, "%Y-%m-%d")
	
	date_list = []
	current_date = start
	
	while current_date <= end:
		date_list.append(current_date.strftime("%Y-%m-%d"))
		current_date += timedelta(days=1)
	
	return date_list


def build_url(date_str):
	"""根据日期构建URL"""
	return f"https://wannianrili.bmcx.com/{date_str}__wannianrili/"


def fetch_html_from_url(url):
	"""从URL获取HTML内容"""
	try:
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
		}
		response = requests.get(url, headers=headers, timeout=10)
		response.raise_for_status()  # 如果请求失败则抛出异常
		response.encoding = 'utf-8'  # 确保正确编码
		return response.text
	except requests.exceptions.RequestException as e:
		print(f"请求URL时出错: {e}")
		return None


def parse_lunar_date(lunar_date_str):
	"""解析农历日期，拆分为月份和日期"""
	if not lunar_date_str:
		return "", ""
	
	# 匹配农历月份和日期
	# 支持格式：正月、二月、三月...腊月 + 初一、初二...三十
	match = re.search(r'^(.*?月)(.*)$', lunar_date_str)
	if match:
		lunar_month = match.group(1)  # 农历月份
		lunar_day = match.group(2)  # 农历日期
		return lunar_month, lunar_day
	else:
		# 如果无法解析，返回原始字符串作为月份，日期为空
		return lunar_date_str, ""


def extract_calendar_info(html_content, target_date):
	"""从HTML内容中提取日历信息"""
	if not html_content:
		return None
	
	# 计算ID
	day = int(target_date.split('-')[-1])
	id = day - 1
	
	soup = BeautifulSoup(html_content, 'html.parser')
	
	# 查找包含日历信息的容器
	main_div = soup.find('div', id=f'wnrl_k_you_id_{id}')
	
	if not main_div:
		# 如果找不到特定ID，尝试查找类似的类
		main_div = soup.find('div', class_='wnrl_k_you')
		if not main_div:
			print(f"未找到日历容器，日期: {target_date}")
			return None
	
	# 提取各个部分
	result = {'日期': target_date}
	
	# 日期标题 - 提取年、月、星期和月大小
	biaoti = main_div.find('div', class_='wnrl_k_you_id_biaoti')
	if biaoti:
		biaoti_text = biaoti.get_text(strip=True)
		# 解析日期标题
		match = re.search(r'(\d{4})年\s*(\d{1,2})月\s*\((.*?)\)\s*(星期.*)', biaoti_text)
		if match:
			year, month, month_size, weekday = match.groups()
			result['年'] = year
			result['月'] = month
			result['月大小'] = month_size
			result['星期'] = weekday
		else:
			# 如果正则匹配失败，尝试直接使用文本
			result['日期标题'] = biaoti_text
	
	# 公历日期 - 提取日
	riqi = main_div.find('div', class_='wnrl_k_you_id_wnrl_riqi')
	if riqi:
		result['日'] = riqi.get_text(strip=True)
	
	# 农历日期 - 拆分为月份和日期
	nongli = main_div.find('div', class_='wnrl_k_you_id_wnrl_nongli')
	if nongli:
		lunar_date_str = nongli.get_text(strip=True)
		lunar_month, lunar_day = parse_lunar_date(lunar_date_str)
		result['农历月份'] = lunar_month
		result['农历日期'] = lunar_day
		result['农历完整日期'] = lunar_date_str  # 保留完整农历日期
	
	# 干支纪年 - 拆分为干支年、生肖年、干支月、干支日
	ganzhi = main_div.find('div', class_='wnrl_k_you_id_wnrl_nongli_ganzhi')
	if ganzhi:
		ganzhi_text = ganzhi.get_text(strip=True)
		# 解析干支纪年
		match = re.search(r'(\S+年)\s*【(\S+)】\s*(\S+月)\s*(\S+日)', ganzhi_text)
		if match:
			ganzhi_year, zodiac_year, ganzhi_month, ganzhi_day = match.groups()
			result['干支年'] = ganzhi_year.replace('年', '')
			result['生肖年'] = zodiac_year.replace('年', '')
			result['干支月'] = ganzhi_month.replace('月', '')
			result['干支日'] = ganzhi_day.replace('日', '')
		else:
			result['干支纪年'] = ganzhi_text
	
	# 节日信息
	jieri_div = main_div.find('div', class_='wnrl_k_you_id_wnrl_jieri')
	festivals = []
	if jieri_div:
		jieri_links = jieri_div.find_all('a')
		for link in jieri_links:
			festivals.append(link.get_text(strip=True))
		result['节日'] = ", ".join(festivals)
	else:
		result['节日'] = ""
	
	return result


def save_to_csv(data_list, filename):
	"""将数据保存为CSV文件"""
	if not data_list:
		print("没有数据可保存")
		return
	
	# 获取所有可能的字段名
	fieldnames = set()
	for data in data_list:
		fieldnames.update(data.keys())
	
	# 确保日期字段在最前面
	fieldnames = ['日期'] + [f for f in sorted(fieldnames) if f != '日期']
	
	try:
		with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for data in data_list:
				writer.writerow(data)
		print(f"数据已保存到: {filename}")
	except Exception as e:
		print(f"保存CSV文件时出错: {e}")


def process_month_dates(month_dates):
	"""处理一个月内的所有日期"""
	month_results = []
	html_content = None
	
	for i, date in enumerate(month_dates):
		# 如果是该月的第一天，获取整个月的HTML内容
		if i == 0:
			url = build_url(date)
			html_content = fetch_html_from_url(url)
			if not html_content:
				print(f"无法获取 {date} 的HTML内容，跳过该月")
				break
		
		if html_content:
			calendar_info = extract_calendar_info(html_content, date)
			if calendar_info:
				month_results.append(calendar_info)
				print(f"成功提取 {date} 的数据")
			else:
				print(f"未能提取 {date} 的数据")
		
		# 添加小延时，避免请求过快
		time.sleep(0.1)
	
	return month_results


def group_dates_by_month(date_range):
	"""按月份分组日期"""
	months = {}
	for date in date_range:
		# 提取年月作为键
		year_month = date[:7]  # YYYY-MM
		if year_month not in months:
			months[year_month] = []
		months[year_month].append(date)
	return months


def main():
	"""主函数"""
	# 获取用户输入的日期范围
	print("请输入日期范围 (格式: YYYY-MM-DD)")
	start_date = '2018-01-01'
	end_date = '2026-01-01'
	
	# 验证日期格式
	try:
		datetime.strptime(start_date, "%Y-%m-%d")
		datetime.strptime(end_date, "%Y-%m-%d")
	except ValueError:
		print("日期格式错误，请使用 YYYY-MM-DD 格式")
		return
	
	# 生成日期范围
	date_range = generate_date_range(start_date, end_date)
	print(f"将处理 {len(date_range)} 天的数据")
	
	# 按月份分组
	months = group_dates_by_month(date_range)
	print(f"共 {len(months)} 个月需要处理")
	
	# 存储所有数据
	all_data = []
	
	# 设置线程数（根据网络情况和目标网站承受能力调整）
	max_workers = 5  # 保守的线程数，避免对目标网站造成过大压力
	
	# 使用线程池处理每个月的数据
	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		# 提交所有任务
		future_to_month = {
			executor.submit(process_month_dates, month_dates): month
			for month, month_dates in months.items()
		}
		
		# 处理完成的任务
		completed = 0
		total = len(months)
		
		for future in as_completed(future_to_month):
			month = future_to_month[future]
			try:
				month_results = future.result()
				all_data.extend(month_results)
				completed += 1
				print(f"已完成月份 {month} 的处理 ({completed}/{total})")
			except Exception as e:
				print(f"处理月份 {month} 时出错: {e}")
	
	# 按日期排序
	all_data.sort(key=lambda x: x['日期'])
	
	# 保存为CSV文件
	if all_data:
		filename = f"calendar_data_{start_date}_to_{end_date}.csv"
		save_to_csv(all_data, filename)
		print(f"\n成功处理 {len(all_data)} 天的数据")
		
		# 显示前几行数据作为预览
		print("\n数据预览 (前3行):")
		for i, data in enumerate(all_data[:3]):
			print(f"\n第{i + 1}行:")
			for key, value in data.items():
				print(f"  {key}: {value}")
	else:
		print("没有成功提取到任何数据")


if __name__ == "__main__":
	main()