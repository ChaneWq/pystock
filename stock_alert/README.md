# Stock Alert 系统

这是一个基于 Python 的**股价提醒系统**，支持：
- 监控一个或多个股票代码，按用户设定的条件（如价格大于、价格小于、涨幅/跌幅百分比）进行检测；
- 当条件首次触发时，通过控制台打印或钉钉 (`DingTalk`) Webhook 发送通知；
- 支持任务新增、删除、列表、重置通知状态；
- 支持 Docker 容器部署。

## 功能一览
- 添加监控任务：股票代码、条件类型（ge, le, change_pct_up, change_pct_down）、监控频率（秒）、通知方式（console / dingtalk）、可选备注；
- 列出所有任务，展示任务状态、是否已通知；
- 删除任务；
- 启动监控，系统每隔指定频率拉取当前价格，首次满足条件即通知；
- 重置所有任务的 “已通知” 状态，使任务可再次触发；
- 任务存储于 `tasks.json` 文件，重启后仍可继续监控。

## 快速开始

### 本地运行
1. 安装依赖：
   ```bash
   pip install -r requirements.txt


下面是你这款“股价提醒系统”项目的**说明文档草案**，适合放在项目根目录（如 `docs/` 或 `README.md` 内的子节）来方便后续开发、修改和扩展。你可以根据实际代码稍作调整。

---

# 项目说明文档

## 1. 项目概述

本项目为一款基于 Python 的“股价提醒系统”，其核心功能为：用户可指定一个或多个股票代码及其触发条件（如价格 ≥ X、价格 ≤ Y、涨幅 ≥ Z% 等），系统定期查询该股票当前价格，当首次满足条件时，通过控制台打印或通过 钉钉（DingTalk）机器人 Webhook 推送通知，并记录“已通知”状态，避免重复提醒。用户可通过菜单方式新增、删除、列出任务、重置提醒状态、启动监控。

系统旨在日常监控场景中减少盯盘成本，而不是毫秒级高频交易参考。未来可扩展为邮件、短信、复杂条件、多用户、多任务调度等。

---

## 2. 功能描述

### 2.1 用户功能

* 列出所有监控任务（显示任务 ID、股票代码、条件、频率、通知方式、Webhook 地址、备注、是否已通知）。
* 新增监控任务：输入股票代码、条件类型（`ge`、`le`、`change_pct_up`、`change_pct_down`）、值、监控频率（秒）、通知方式（`console` 或 `dingtalk`）、若选择 dingtalk 则输入 Webhook URL、并可输入备注（可为空）。
* 删除任务：通过任务 ID 删除。
* 启动监控：系统开始监控所有已启用任务，每隔一定秒数（当前实现为全局频率或可按任务频率）拉取股票当前价、评估触发条件、若首次满足条件则通知并标记“已通知”。
* 重置所有任务通知状态：将所有任务的 `notified` 字段设为 False，使它们可重新触发通知。

### 2.2 系统后台功能

* 存储任务信息（当前使用本地 JSON 文件 `tasks.json`）。
* 定期拉取股票价格：调用已有接口 `get_cur_price(stock_code, client)`。
* 条件判断模块：支持价格阈值比较、涨跌幅度比较。
* 通知模块：支持控制台打印和 dingtalk Webhook 推送。
* 任务管理模块：新增、删除、列出、更新。
* 配置模块：包含默认频率、任务文件路径等。
* 日志与异常处理：监控过程中对获取失败、网络异常、API 异常进行记录和提示。

---

## 3. 系统架构 & 模块说明

### 3.1 模块结构

```
config.py            — 系统常量配置（如默认监控频率、任务文件名）  
storage.py           — 负责任务数据的存取（加载／保存 JSON）  
task_manager.py      — 任务管理接口（新增、删除、修改、列表）  
fetcher.py           — 封装价格获取接口（初始化客户端、查询当前价）  
notifier.py          — 通知模块（控制台通知、钉钉 Webhook 通知）  
scheduler.py         — 调度模块（启动监控循环、遍历任务、调用 fetcher + 判断 + notifier）  
main.py              — 命令行菜单交互入口（列出任务、新增、删除、启动监控、重置通知状态、退出）  
tasks.json           — 存储任务数据的文件（JSON 格式）  
```

### 3.2 关键数据结构

每个任务（Task）在 `tasks.json` 内的典型 JSON 格式示例：

```json
{
  "task_id": "f55177ce-ef5d-4e2a-9dcc-d0255b73c86e",
  "stock_code": "000400",
  "condition": {
    "type": "ge",
    "value": 1.0
  },
  "frequency_sec": 3,
  "notify_method": "dingtalk",
  "dingtalk_webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=…",
  "last_price": 28.89,
  "enabled": true,
  "notified": true,
  "remark": "这是一个备注"
}
```

字段说明：

* `task_id`：任务唯一识别 ID（UUID）。
* `stock_code`：股票代码字符串。
* `condition`：监控条件，`type` 表示类型（`ge`：≥、`le`：≤、`change_pct_up`：涨幅 ≥、`change_pct_down`：跌幅 ≥），`value` 为比较值（如 20.5 表示 ≥20.5 元或涨幅 ≥20.5%）。
* `frequency_sec`：监控频率（秒数）。
* `notify_method`：通知方式，`console` 或 `dingtalk`。
* `dingtalk_webhook_url`：如通知方式为 dingtalk，则配置该 Webhook URL；否则为 null 或空字符串。
* `last_price`：上次拉取到的价格，用于“涨幅／跌幅”类型判断；初始为 null。
* `enabled`：任务是否启用（布尔）。若为 false，调度器跳过该任务。
* `notified`：是否已发送过通知（布尔）。当首次触发通知后设为 true，后续即便条件仍满足不会再次通知。
* `remark`：备注信息（可为空字符串）。通知时会显示。

### 3.3 控制流程（简化流程图版）

1. 用户运行 `main.py` 并选择菜单“启动监控”。
2. 调度器初始化客户端（`fetcher.init_create_client()`）并进入循环。
3. 每次迭代：

   * 加载当前任务列表（`storage.load_tasks()`）。
   * 遍历每条任务：

     * 如果 `enabled` 为 false，跳过。
     * 如果 `notified` 已为 true，跳过通知，只更新 `last_price`。
     * 获取当前价格（`fetcher.get_current_price(stock_code, client)`）。
     * 调用条件判断模块（`evaluate_condition(task, current_price)`）：返回 (`triggered`, `reason`)。
     * 如果 `triggered == true` 且 `notified == false`：发送通知（`notifier.notify(...)`）、将 `task["notified"] = true`。
     * 更新 `task["last_price"] = current_price`。
   * 保存任务列表（`storage.save_tasks()`）。
   * 线程 sleep 或按频率等待下一轮。

### 3.4 设计决策与扩展考虑

* **首次触发后不重复提醒**：通过 `notified` 字段实现。若未来希望“价格回落后再触发”可加入重置条件（例如当价格回落 X %后将 notified 设为 false）。
* **频率管理**：当前实现为统一频率或者每任务频率但采用简单 sleep 机制。若任务量或频率较高，可考虑使用定时调度库（如 APScheduler）或异步机制。
* **通知方式扩展**：目前支持控制台和 dingtalk。未来可扩展邮箱、短信、微信、小程序推送。
* **存储方式**：当前使用 JSON 文件简单持久化；若任务量大、多个用户或并发读写需求，可迁移为 SQLite/MySQL 或某 NoSQL 存储。
* **任务条件扩展**：目前为简单阈值比较或涨跌幅度。后续可支持 “连续 N 次满足”、”移动平均突破”、”成交量变化” 等，更复杂逻辑。
* **代码模块化与可维护性**：模块间职责清晰，易于新增模块与测试。
* **部署方式**：提供 Docker 镜像方案，适合长期运行及容器化部署。

---

## 4. 代码详细说明（按模块）

### 4.1 `config.py`

定义系统使用的常量，如默认监控频率 `DEFAULT_FREQUENCY_SEC`、任务文件名 `TASKS_FILE`。更改默认频率或文件路径时可在此修改。

```python
# config.py
DEFAULT_FREQUENCY_SEC = 60  # 默认每 60 秒监控一次
TASKS_FILE = "tasks.json"   # 任务存储文件
```

### 4.2 `storage.py`

负责任务的加载与保存。使用 JSON 文件存储。

* `load_tasks()`：尝试打开并读取 TASKS_FILE，若不存在则返回空列表。
* `save_tasks(tasks: List[Dict])`：将任务列表写入 TASKS_FILE。
  这样模块隔离了存储细节，未来若替换为数据库，只需修改此模块。

### 4.3 `task_manager.py`

提供任务管理接口：新增、删除、更新、列出任务。

* `add_task(...)`：生成 UUID 作为 task_id，初始化任务的所有字段（包含 `notified=False`、`last_price=None`、`enabled=True`、`remark`）。
* `remove_task(task_id)`：通过 task_id 查找并移除任务。
* `list_tasks()`：直接返回当前任务列表。
* `update_task(task_id, **kwargs)`：修改任务指定字段（如 `enabled`、`remark`、`frequency_sec` 等）。
  将来若加入“重置单个任务提醒状态”功能，可在此模块新增如 `reset_task_notified(task_id)`。

### 4.4 `fetcher.py`

封装从股票接口获取当前价格的逻辑：

* `init_client()`：初始化客户端（调用你已有的 `init_create_client()`）。
* `get_current_price(stock_code, client)`：调用 `get_cur_price(stock_code, client)`，捕获异常并返回 float 价格或 None。
  后续若切换数据源／支持批量拉取，可扩展此模块。

### 4.5 `notifier.py`

通知模块，负责根据任务配置发送提醒：

* `send_notification_console(task, current_price, reason)`：控制台 print。
* `send_dingtalk_message(webhook_url, msg)`：对 dingtalk Webhook 调用 HTTP POST 发送消息。包含基本错误处理。
* `notify(task, current_price, reason)`：根据 `notify_method` 选择合适方式。构造消息时包含备注 `remark`。
  将来可新增如 `send_email(...)`、`send_sms(...)`。

### 4.6 `scheduler.py`

调度模块，负责持续监控任务、调用 fetcher 和 notifier 、控制调度频率。

* `evaluate_condition(task, current_price)`：根据任务 condition 判断是否触发，返回 `(bool triggered, str reason)`。支持四种 type。
* `monitor_task(task, client)`：如果任务已通知 (`notified=True`)，则跳过通知；否则获取当前价、判断、发送通知、更新 last_price、标记 notified。
* `start_monitoring()`：初始化客户端，进入循环：加载任务、遍历任务、调用 monitor_task、保存任务列表、等待下次。当前使用 time.sleep() 控制频率，简单实现。
  若支持每任务不同频率、异步或批量拉取，可在此模块升级。

### 4.7 `main.py`

命令行菜单交互入口，展现菜单、接收用户输入、调用 task_manager 、启动监控。功能包括：

* 列出任务（调用 list_tasks_pretty()）。
* 添加任务（输入股票、条件、频率、通知方式、Webhook（如需要）、备注）。
* 删除任务（输入任务 ID）。
* 启动监控（调用 scheduler.start_monitoring()，进入监控循环）。
* 重置所有任务通知状态（调用 reset_all_notified()）。
* 退出。
  该模块负责用户界面交互逻辑，后续如改为 Web 前端／GUI，可替换此模块。

---

## 5. 开发与扩展指南

### 5.1 如何新增通知方式

1. 在 `notifier.py` 新增发送函数（如 `send_email_message(...)`）。
2. 在 `notify(task, …)` 中增加对应 notify_method 分支（如 `"email"`）。
3. 在 `task_manager.add_task()` 和 main菜单中让用户选择新增方式。
4. 更新任务数据结构以包含新方式所需字段（如 `email_address`）。
5. 更新 README 和说明文档。

### 5.2 如何支持新条件类型

1. 在 `scheduler.evaluate_condition()` 中增加新的 type 处理逻辑（如 `"volume_up"`, `"ma_crossover"` 等）。
2. 在任务新增菜单中提示用户选择新类型，并在 condition 字段中设置。
3. 若条件需要额外数据（如成交量、均线），可能需要在 fetcher.py 增加相应 API 支持。
4. 测试：新增任务后模拟触发情形，验证通知逻辑。

### 5.3 如何支持任务级别不同频率

当前仅使用全局 frequency_sec。若想每任务执行自定义频率：

* 在 `scheduler.start_monitoring()` 创建每任务 Thread 或 Timer，按 task["frequency_sec"] 分别调度。
* 或使用 APScheduler 等库，按任务调度。
* 注意：若任务频率差别大或任务数多，需避免频繁拉取重叠、控制资源消耗。

### 5.4 如何切换存储方式为数据库

* 把 storage.py 改为访问 SQLite/MySQL 接口。
* 任务管理接口（task_manager.py）简化对 storage 模块的方法调用。
* 迁移时需数据迁移脚本，把 tasks.json 内容导入数据库。
* 注意并发读写、事务管理。

### 5.5 如何部署、运维

* 使用 Docker 镜像部署：见 Dockerfile。注意挂载 tasks.json 以持久化任务。
* 日志机制：目前仅 print，建议改用 Python `logging` 模块记录日志、轮转。
* 异常监控：如 fetcher 连续失败、 dingtalk 请求失败、网络异常，应报警或恢复策略。
* 健康检查：可设计监控接口或脚本，检查进程是否运行、任务是否执行、提醒逻辑有效。

---

## 6. 术语表

| 术语                   | 含义                                            |
| -------------------- | --------------------------------------------- |
| 任务 (Task)            | 用户定义的监控项，包括股票代码、条件、频率、通知方式、备注等。               |
| 条件 (Condition)       | 任务中指定的触发规则，如价格 ≥ X。                           |
| 通知方式 (Notify Method) | 触发提醒时使用的渠道，如控制台 (console)、钉钉 (dingtalk)。      |
| Webhook              | 钉钉机器人提供的接口 URL，用于向群组发送消息。                     |
| 已通知 (Notified)       | 布尔字段，标记任务是否已经触发并发送提醒。若为 true，则后续即便条件满足也不重复通知。 |
| 监控频率 (Frequency)     | 系统查询该股票价格的时间间隔（秒数）。                           |

---

## 7. 联系与贡献

如果你／团队将来要增强此项目，建议遵循以下流程：

* 每次新增功能或修改设计，先在 README 或专门 docs/architecture.md 中更新说明（保持文档与代码同步）— 好文档能避免日后维护困难。 ([Atlassian][1])
* 编写单元测试以保证改动不会破坏现有功能。
* 在 GitHub 或代码仓库使用 Issue 和 Pull Request 流程，清晰描述变更目的。
* 如果任务量或用户数量增长，考虑将系统模块化拆分、引入服务化、使用消息队列、异步处理等。

---

