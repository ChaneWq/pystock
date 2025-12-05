# monitor_stock_fixed.py
import sys
import os
import csv
import time

# 如果 day_index 在上层目录（与你原来写法一致），保持导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from day_index import init_create_client, get_price_and_change_percent

def clear_screen():
    """跨平台清屏：Windows 使用 cls，其他系统使用 clear"""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def read_stock_data_from_csv(file_path):
    """
    从CSV文件读取股票代码和名称

    参数:
        file_path: CSV文件路径

    返回:
        list: 包含 (code, name) 元组的列表
    """
    stock_data = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get('code') and row.get('name'):
                    stock_data.append((row['code'], row['name']))
        return stock_data
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return []
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        return []

def format_stock_line(code, name, price, change):
    """
    格式化单行股票显示，保留颜色与符号
    返回：格式化字符串（已包含颜色复位）
    """
    reset = "\033[0m"
    if change > 0:
        color_code = "\033[92m"  # 绿色
        change_symbol = "↑"
    elif change < 0:
        color_code = "\033[91m"  # 红色
        change_symbol = "↓"
    else:
        color_code = "\033[0m"
        change_symbol = "→"

    # 保证格式对齐：你可根据需要调整宽度
    # return f"{code:8s} {name:20s} {price:8.2f} {color_code}{change_symbol} {change:+6.2f}%{reset}"
    return f"{code:8s} {name:20s} {price:8.2f} {change:+6.2f}{reset}"

def monitor_stock_prices(stock_data, interval):
    """
    定期监控并在同一位置刷新显示多只股票的价格和涨跌幅

    参数:
        stock_data: 包含 (code, name) 元组的列表
        interval: 时间间隔(秒)
    """
    if not stock_data:
        print("没有找到有效的股票数据")
        return

    client = init_create_client()

    try:
        # 主循环
        while True:
            # 先清屏，再重绘整个显示区域（标题 + 每只股票一行）
            clear_screen()

            # 标题行（包含更新时间）
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            # header = f"股票监控 - 数量: {len(stock_data)}    更新时间: {now}"
            # print(header)
            # print("-" * len(header))

            # 获取并打印所有股票的最新数据（每只一行）
            for code, name in stock_data:
                try:
                    price, change = get_price_and_change_percent(code, client)
                    line = format_stock_line(code, name, price, change)
                except Exception as e:
                    # 获取失败时显示错误信息，但仍占据一行
                    line = f"{code:8s} {name:20s} 获取失败: {str(e)}"
                print(line)

            # 底部提示（不占用无穷行）
            print("\n按 Ctrl+C 停止监控", flush=True)

            # 强制刷新输出缓冲区，确保即时更新
            sys.stdout.flush()

            # 等待下一轮
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    # 从CSV文件读取股票代码和名称
    csv_file = "config.csv"  # CSV文件路径（按需更改）
    stock_data = read_stock_data_from_csv(csv_file)

    if stock_data:
        # 设置时间间隔（秒）
        interval_seconds = 2  # 你原来使用1秒间隔，这里保持不变
        monitor_stock_prices(stock_data, interval_seconds)
    else:
        print("未找到有效的股票数据，程序退出")
