import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from day_index import get_cur_price,init_create_client,get_cur_data
import requests
import json
import time
client = init_create_client()
while(True):
	time.sleep(1)
	print(get_cur_price("002670",client))
	open, close, high, low, vol, amount, year, month, day, hour, minute, datetime, volume = get_cur_data('000400',client)

