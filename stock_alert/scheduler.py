# scheduler.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import threading
import task_manager
import fetcher
import notifier
from config import DEFAULT_FREQUENCY_SEC

def evaluate_condition(task, current_price: float) -> (bool, str):
    cond = task["condition"]
    ctype = cond.get("type")
    value = cond.get("value")
    last_price = task.get("last_price")
    if current_price is None:
        return False, ""
    if ctype == "ge":
        if current_price >= value:
            # return True, f"price >= {value}"
            return True, f"b >= {value}"
    elif ctype == "le":
        if current_price <= value:
            # return True, f"price <= {value}"
            return True, f"b <= {value}"
    elif ctype == "change_pct_up":
        if last_price is not None and (current_price - last_price)/last_price >= value/100.0:
            # return True, f"price ↑ ≥ {value}%"
            return True, f"b ↑ ≥ {value}%"
    elif ctype == "change_pct_down":
        if last_price is not None and (last_price - current_price)/last_price >= value/100.0:
            # return True, f"price ↓ ≥ {value}%"
            return True, f"b ↓ ≥ {value}%"
    # else:
    return False, ""


# scheduler.py
def monitor_task(task, client):
    if not task.get("enabled", True):
        return
    if task.get("notified", False):
        # 已经通知过，此任务跳过通知，仅更新 last_price 或不处理
        current_price = fetcher.get_current_price(task["stock_code"], client)
        task["last_price"] = current_price
        return

    current_price = fetcher.get_current_price(task["stock_code"], client)
    triggered, reason = evaluate_condition(task, current_price)
    if triggered:
        notifier.notify(task, current_price, reason)
        task["notified"] = True  # 标记为已通知
    # 更新 last_price 无论是否触发
    task["last_price"] = current_price


def start_monitoring():
    client = fetcher.init_client()
    while True:
        tasks = task_manager.list_tasks()
        for task in tasks:
            monitor_task(task, client)
            # 可以为每个任务启动线程或串行执行
            monitor_task(task, client)
        # 保存 updated last_price
        task_manager.storage.save_tasks(tasks)
        time.sleep(DEFAULT_FREQUENCY_SEC)
