# notifier.py
import requests
import json

def send_notification_console(task, current_price: float, reason: str):
    print(f"[Notification] Task {task['task_id']} for stock {task['stock_code']} triggered: price={current_price} | reason={reason}")


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


def notify(task, current_price: float, reason: str):
    remark = task.get("remark", "")
    # 构造基础消息
    # base_msg = f"~~~股票 {task['stock_code']} 触发提醒：当前价格 {current_price}，原因：{reason}"
    base_msg = f"~~~sto {task['stock_code']} notify：curp {current_price}，原因：{reason}"
    if remark:
        full_msg = base_msg + f"（备注：{remark}）"
    else:
        full_msg = base_msg

    method = task.get("notify_method", "console")
    if method == "console":
        print(f"[Notification] {full_msg}")
    elif method == "dingtalk":
        webhook_url = task.get("dingtalk_webhook_url")
        if not webhook_url:
            print(f"[Notifier] 任务 {task['task_id']} 使用钉钉通知但未配置 webhook URL。")
            print(f"[Notification] {full_msg}")
        else:
            send_dingtalk_message(webhook_url, full_msg)
    else:
        print(f"[Notifier] 未知通知方式 {method}, 回退到控制台。")
        print(f"[Notification] {full_msg}")

