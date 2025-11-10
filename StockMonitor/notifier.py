# notifier.py
import requests
import json

# def send_dingtalk_message(webhook_url: str, msg: str):
#     headers = {"Content-Type": "application/json"}
#     body = {"msgtype": "text", "text": {"content": msg}}
#     try:
#         resp = requests.post(webhook_url, headers=headers, data=json.dumps(body))
#         resp.raise_for_status()
#         resp_json = resp.json()
#         if resp_json.get("errcode", -1) != 0:
#             print(f"[DingTalk] 发送失败: {resp_json}")
#         else:
#             print(f"[DingTalk] 发送成功: {msg}")
#     except Exception as e:
#         print(f"[DingTalk] 异常发送消息: {e}")


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

def notify(task: dict, current_price: float, reason: str, vol_info: str = ""):
    remark = task.get("remark", "")
    msg = f"~~~股票 {task['stock_code']} 触发提醒：当前价格 {current_price}，原因：{reason}"
    if vol_info:
        msg += f"；量能信息：{vol_info}"
    if remark:
        msg += f"（备注：{remark}）"

    method = task.get("notify_method", "console")
    if method == "console":
        print(f"[Notification] {msg}")
    elif method == "dingtalk":
        webhook_url = task.get("dingtalk_webhook_url")
        if not webhook_url:
            print(f"[Notifier] 任务 {task['task_id']} 使用 dingtalk，但未配置 webhook URL。回退至控制台：")
            print(f"[Notification] {msg}")
        else:
            send_dingtalk_message(webhook_url, msg)
    else:
        print(f"[Notifier] 未知通知方式 {method}，回退至控制台：")
        print(f"[Notification] {msg}")
