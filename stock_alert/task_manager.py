# task_manager.py
import uuid
from typing import Dict, List
import storage
from config import DEFAULT_FREQUENCY_SEC

# def add_task(stock_code: str, condition: Dict, frequency_sec: int = None, notify_method: str = "console") -> str:
#     tasks = storage.load_tasks()
#     task_id = str(uuid.uuid4())
#     if frequency_sec is None:
#         frequency_sec = DEFAULT_FREQUENCY_SEC
#     task = {
#         "task_id": task_id,
#         "stock_code": stock_code,
#         "condition": condition,
#         "frequency_sec": frequency_sec,
#         "notify_method": notify_method,
#         "last_price": None,
#         "enabled": True
#     }
#     tasks.append(task)
#     storage.save_tasks(tasks)
#     return task_id

def remove_task(task_id: str) -> bool:
    tasks = storage.load_tasks()
    new_tasks = [t for t in tasks if t["task_id"] != task_id]
    if len(new_tasks) == len(tasks):
        return False
    storage.save_tasks(new_tasks)
    return True

def list_tasks() -> List[Dict]:
    return storage.load_tasks()

def update_task(task_id: str, **kwargs) -> bool:
    tasks = storage.load_tasks()
    found = False
    for t in tasks:
        if t["task_id"] == task_id:
            for k, v in kwargs.items():
                if k in t:
                    t[k] = v
            found = True
            break
    if found:
        storage.save_tasks(tasks)
    return found

import uuid
from typing import Dict, List
import storage
from config import DEFAULT_FREQUENCY_SEC
def add_task(stock_code: str, condition: Dict,
             frequency_sec: int = None,
             notify_method: str = "console",
             dingtalk_webhook_url: str = None,
             remark: str = "") -> str:
    tasks = storage.load_tasks()
    task_id = str(uuid.uuid4())
    if frequency_sec is None:
        frequency_sec = DEFAULT_FREQUENCY_SEC
    task = {
        "task_id": task_id,
        "stock_code": stock_code,
        "condition": condition,
        "frequency_sec": frequency_sec,
        "notify_method": notify_method,
        "dingtalk_webhook_url": dingtalk_webhook_url,
        "last_price": None,
        "enabled": True,
        "notified": False,
        "remark": remark
    }
    tasks.append(task)
    storage.save_tasks(tasks)
    return task_id
