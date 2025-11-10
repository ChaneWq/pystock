# task_manager.py
import uuid
from typing import Dict, List
import storage

def add_task(stock_code: str, condition: Dict, frequency_sec: int = None,
             notify_method: str = "console", dingtalk_webhook_url: str = None,
             remark: str = "") -> str:
    tasks = storage.load_tasks()
    task_id = str(uuid.uuid4())
    if frequency_sec is None:
        frequency_sec = 5  # 默认 5 秒，可根据需要修改
    task = {
        "task_id": task_id,
        "stock_code": stock_code,
        "condition": condition,
        "frequency_sec": frequency_sec,
        "notify_method": notify_method,
        "dingtalk_webhook_url": dingtalk_webhook_url,
        "last_price": None,
        "last_vol": None,
        "enabled": True,
        "notified": False,
        "remark": remark
    }
    tasks.append(task)
    storage.save_tasks(tasks)
    return task_id

def remove_task(task_id: str) -> bool:
    tasks = storage.load_tasks()
    new_tasks = [t for t in tasks if t["task_id"] != task_id]
    if len(new_tasks) == len(tasks):
        return False
    storage.save_tasks(new_tasks)
    return True

def list_tasks() -> List[Dict]:
    return storage.load_tasks()

def clear_all_tasks() -> None:
    storage.save_tasks([])

def reset_all_notified() -> int:
    tasks = storage.load_tasks()
    count = 0
    for t in tasks:
        if t.get("notified", False):
            t["notified"] = False
            count += 1
    storage.save_tasks(tasks)
    return count
