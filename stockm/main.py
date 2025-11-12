# main.py
import task_manager

def format_task(t):
    cond = t["condition"]
    cond_str = ""
    if cond["type"] == "ge":
        cond_str = f"≥ {cond['value']}"
    elif cond["type"] == "le":
        cond_str = f"≤ {cond['value']}"
    elif cond["type"] == "change_pct_up":
        cond_str = f"涨幅 ≥ {cond['value']}%"
    elif cond["type"] == "change_pct_down":
        cond_str = f"跌幅 ≥ {cond['value']}%"
    elif cond["type"] == "vol_up":
        cond_str = f"量能 ≥ 前一日 × {cond['value']}"
    else:
        cond_str = str(cond)

    webhook = t.get("dingtalk_webhook_url") or "—"
    notify = t.get("notify_method") or "console"
    notified = "Yes" if t.get("notified") else "No"
    remark = t.get("remark", "")

    return (
        f"{t['task_id']} | {t['stock_code']} | {cond_str} | {t['frequency_sec']}s | "
        f"{notify} | {webhook} | 已通知={notified} | 备注={remark}"
    )

def list_tasks_pretty():
    tasks = task_manager.list_tasks()
    if not tasks:
        print("当前无监控任务。")
        return
    print("任务ID | 股票代码 | 条件 | 频率 | 通知方式 | Webhook／URL | 已通知 | 备注")
    print("-" * 120)
    for t in tasks:
        print(format_task(t))
    print("-" * 120)

def print_menu():
    print("1. 列出任务")
    print("2. 添加任务")
    print("3. 删除任务")
    print("4. 启动监控")
    print("5. 重置所有任务通知状态")
    print("6. 清空所有任务（需二次确认）")
    print("0. 退出")


def main():
    while True:
        print_menu()
        choice = input("选择操作: ").strip()
        if choice == "1":
            list_tasks_pretty()
        elif choice == "2":
            stock = input("股票代码（例如 600900）: ").strip()
            print("条件类型: ge(>=), le(<=), change_pct_up(涨幅≥), change_pct_down(跌幅≥), vol_up(量能放大≥前一日×倍数)")
            ctype = input("type: ").strip()
            val = float(input("value: ").strip())
            freq = input("监控频率（秒，留空用默认5秒）: ").strip()
            freq = int(freq) if freq else None
            print("通知方式: console（控制台）或 dingtalk（钉钉）")
            method = input("notify_method: ").strip()
            method = 'dingtalk'
            webhook = None
            if method == "dingtalk":
                webhook = input("请输入钉钉机器人 webhook URL: ").strip()
                webhook = 'https://oapi.dingtalk.com/robot/send?access_token=4471836ef0e71d1cfcbccce0589854cb0089bcbc9a1cf961bf67ccdc915dae62'
            remark = input("备注（直接回车则为空）: ").strip()
            cond = {"type": ctype, "value": val}
            task_id = task_manager.add_task(stock, cond, frequency_sec=freq,
                                            notify_method=method, dingtalk_webhook_url=webhook,
                                            remark=remark)
            print("任务添加，ID =", task_id)
        elif choice == "3":
            tid = input("输入任务ID: ").strip()
            if task_manager.remove_task(tid):
                print("已删除任务", tid)
            else:
                print("任务ID 未找到", tid)
        elif choice == "4":
            print("启动监控 (按 Ctrl-C 停止)…")
            import scheduler
            scheduler.start_monitoring()
            break
        elif choice == "5":
            count = task_manager.reset_all_notified()
            print(f"已将 {count} 条任务的通知状态重置为 False。")
        elif choice == "6":
            confirm = input("你确定要清空所有任务吗？此操作不可恢复。输入 'yes' 确认: ").strip().lower()
            if confirm == "yes":
                task_manager.clear_all_tasks()
                print("已清空所有任务。")
            else:
                print("取消清空操作。")
        elif choice == "0":
            print("退出程序。")
            break
        else:
            print("无效选择，请重试。")

if __name__ == "__main__":
    main()
