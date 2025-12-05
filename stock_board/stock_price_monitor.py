import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from day_index import init_create_client, get_price_and_change_percent


def monitor_stock_price(code, interval):
    """
    定期监控并打印股票价格和涨跌幅
    
    参数:
    code: 股票代码
    interval: 时间间隔(秒)
    """
    client = init_create_client()
    
    # print(f"开始监控股票 {code}，每隔 {interval} 秒更新一次")
    print("=" * 50)
    try:
        while True:
            price, change = get_price_and_change_percent(code, client)
            # 使用 \r 回到行首，end='' 避免换行，flush=True 立即刷新输出
            # print(f"\r当前价格: {price:.2f}, 涨跌幅: {change:.2f}%", end='', flush=True)
            print(f"\rcp: {price:.2f}, fd: {change:.2f}", end='', flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        # 在退出前添加换行，避免与提示信息在同一行
        print("\n监控已停止")


if __name__ == "__main__":
	# 使用input方式获取用户输入
	# stock_code = input("请输入股票代码: ")
	stock_code = input("c: ")
	# interval_seconds = int(input("请输入时间间隔(秒): "))
	interval_seconds = int(input("s"))
	
	monitor_stock_price(stock_code, interval_seconds)