# -*- coding: utf-8 -*-
import pymysql
from datetime import datetime
import requests
import json

webhook_url_talk = "https://oapi.dingtalk.com/robot/send?access_token=4471836ef0e71d1cfcbccce0589854cb0089bcbc9a1cf961bf67ccdc915dae62"


def mysql_read(query_sql):
    # 数据库连接参数
    db_config = {
    'host' : '10.1.3.40',
    'port' : 9030,
    'user' : 'gzqp_bigdata_prod',
    'password' : 'bg3c1jqy_FGX.m5#mdz',
    'database' : 'gzqp_bigdata_prod'
        # 'host': '%doris_gzqp_bigdata_host%',  # 数据库主机地址
        # 'port': %doris_gzqp_bigdata_port%,  # 数据库端口
        # 'user': '%doris_gzqp_bigdata_username%',  # 数据库用户名
        # 'password': '%doris_gzqp_bigdata_password%',  # 数据库密码
        # 'database': '%doris_gzqp_bigdata_dbname%'  # 要连接的数据库名
    }
    
    # 建立数据库连接
    connection = pymysql.connect(**db_config)
    # 创建游标对象
    with connection.cursor() as cursor:
	    sql = query_sql
	    cursor.execute(sql)
	    results = cursor.fetchall()
    
    # 关闭数据库连接
    if connection.open:
	    connection.close()
    return results


def send_dingtalk_message(webhook_url, message):
	headers = {
		"Content-Type": "application/json",
		"Charset": "UTF-8"
	}
	
	# 消息类型为text
	data = {
		"msgtype": "text",
		"text": {
			"content": message
		}
	}
	
	response = requests.post(url=webhook_url, data=json.dumps(data), headers=headers)
	if response.status_code == 200:
		response_data = response.json()
		if response_data.get('errcode') == 0:
			print("消息发送成功")
			print('发送成功！！')
		else:
			print(f"消息发送失败，错误代码: {response_data.get('errcode')}, 错误信息: {response_data.get('errmsg')}")
	else:
		print(f"消息发送失败，状态码: {response.status_code}, 响应内容: {response.text}")


if __name__ == '__main__':
	config1 = mysql_read("""select distinct shop_name
from gzqp_admin_prod.amazon_listing_report_orig
where dt = current_date()
          """)
	today_shop_list = [item[0] for item in config1]
	necessary = ['Amazon-利天XenovateCor', 'Amazon-畅煜PRFMNCR', 'Amazon-赋冬cwwnbn', 'Amazon-弓长Rlimerance', 'Amazon-小奥MSETRKXG', 'Amazon-黛温DREAM_DYNAMOS', 'Amazon-立欣CARSUDO', 'Amazon-春嬉Kmesonoxian', 'Amazon-瑞光DUANGKAKA', 'Amazon-净茗AXOMELIEFO', 'Amazon-三丰Qovjjndd', 'Amazon-陶琪HDTROFODR', 'Amazon-薯了QuRuCar', 'Amazon-玥琪LIGSHOCAXL', 'Amazon us 纵腾', 'Amazon-璎版VORMORNIX', 'Amazon-福美FJ-Manmiao']
	
	# 今天是否都包含必要店铺
	a = set(necessary).issubset(set(today_shop_list))
	print(a)
	
	# print(today_shop_list)
	# print(11111)
	# bundle_all_ct = round(config1[0][0], 2)
	
	
	# msg = f"""==6.19后新入库图片订单统计==
    # 参考编码总数量：{bundle_all_ct}"""
	
    
	# print(msg)
	
	# send_dingtalk_message(webhook_url_talk, msg)
	# send_dingtalk_message(webhook_url_talk, '~~~1')
	
	