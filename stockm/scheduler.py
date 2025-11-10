# scheduler.py
import time
import task_manager
import storage
import notifier
from day_index import get_cur_data,init_create_client


def evaluate_condition(task: dict, current_data, prev_data) -> (bool, str, str):
    """
    返回 (triggered, price_reason, vol_reason)
    - price_reason: 价格触发原因字符串（若触发价格条件）
    - vol_reason: 量能触发原因字符串（若触发量能条件）
    """
    cond = task["condition"]
    ctype = cond.get("type")
    value = cond.get("value")
    price_reason = ""
    vol_reason = ""
    # 判断价格条件
    if ctype in ("ge", "le", "change_pct_up", "change_pct_down"):
        if prev_data.empty:
            return False, "", ""
        prev_close = prev_data.get("prev_close", None)
        cur_close = current_data.get("close", None)
        if cur_close is None or prev_close is None:
            return False, "", ""
        if ctype == "ge" and cur_close >= value:
            price_reason = f"价格 ≥ {value}"
        elif ctype == "le" and cur_close <= value:
            price_reason = f"价格 ≤ {value}"
        elif ctype == "change_pct_up" and (cur_close - prev_close)/prev_close >= value/100.0:
            price_reason = f"涨幅 ≥ {value}%"
        elif ctype == "change_pct_down" and (prev_close - cur_close)/prev_close >= value/100.0:
            price_reason = f"跌幅 ≥ {value}%"
    # 判断量能条件
    if ctype == "vol_up":
        if prev_data.empty:
            return False, "", ""
        prev_vol = prev_data.get("prev_vol", None)
        cur_vol = current_data.get("vol", None)
        if cur_vol is None or prev_vol is None:
            return False, "", ""
        if cur_vol >= prev_vol * value:
            vol_reason = f"成交量 ≥ 前一日 × {value}"
    triggered = bool(price_reason or vol_reason)
    reason = price_reason or vol_reason
    return triggered, reason, vol_reason

def monitor_task(task: dict, client):
    if not task.get("enabled", True):
        return
    if task.get("notified", False):
        # 已通知过，无需再通知，仍更新 last data
        cur_data, prev_data = get_cur_data(task["stock_code"], client)
        # 更新 last_price / last_vol 可选
        task["last_price"] = cur_data.get("close", None)
        task["last_vol"] = cur_data.get("vol", None)
        return
    cur_data, prev_data = get_cur_data(task["stock_code"], client)
    if cur_data.empty or prev_data.empty:
        # 无效数据跳过
        return
    cur_close = cur_data.get("close", None)
    triggered, reason, vol_reason = evaluate_condition(task, cur_data, prev_data)
    if triggered:
        notifier.notify(task, cur_close, reason, vol_info=vol_reason)
        task["notified"] = True
    # 更新 last values
    task["last_price"] = cur_close
    task["last_vol"] = cur_data.get("vol", None)

def start_monitoring(client=None):
    if client is None:
        client = init_create_client()  # 根据你的实际客户端初始化方式
    print("[Scheduler] 启动监控...")
    while True:
        tasks = task_manager.list_tasks()
        for task in tasks:
            monitor_task(task, client)
        storage.save_tasks(tasks)
        # 可以考虑按最短频率sleep，也可精细改为每任务按频率处理
        time.sleep(5)
