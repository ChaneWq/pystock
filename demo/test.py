import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from day_index import get_cur_price,init_create_client
import requests
import json

client = init_create_client()
print(get_cur_price("600900",client))

