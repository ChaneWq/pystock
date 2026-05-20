# 强势股策略扫描工具 - 参数说明

## 快速开始

```bash
python main.py --strategy vr_slope --file codes.txt --date 20260519
```
python main.py --strategy vr_slope --file codes.txt --date 20260520 --vr_slope_window 4 --vr_slope 4  --vr_slope_min_hits 

--change_max 3
---

## 通用参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy` | string | 必填 | 策略ID，可选：`vp_sync`、`vp_pulse`、`vr_slope` |
| `--file` | string | 必填 | 股票代码文件路径，每行一个代码 |
| `--date` | string | 今天 | 日期，格式 YYYYMMDD |
| `--n` | int | 5 | 过去n个交易日，用于计算分钟均量 |
| `--csv` | flag | 否 | 导出CSV到data目录 |
| `--until` | string | 全天 | 截至时间，格式 HH:MM，模拟盘中该时间点运行 |
| `--no_filter` | flag | 否 | 不过滤创业板(300/301)、科创板(688)、北交所(9开头) |
| `--change_min` | float | -100 | 涨幅下限(%)，低于此值排除 |
| `--change_max` | float | 100 | 涨幅上限(%)，高于此值排除（防追高） |

### 通用参数详解

**`--until`**：模拟盘中运行，截断分时数据到指定时间。例如 `--until 10:00` 只看09:30-10:00的数据，涨幅也以10:00的价格计算。

**`--change_min` / `--change_max`**：涨幅范围过滤，在策略评估通过后判断。涨幅 = (最新价 - 昨收价) / 昨收价 × 100%。典型用法：
- `--change_min 0 --change_max 7`：只看上涨但不超过7%的，防追高
- `--change_max 5`：排除涨幅超过5%的
- `--change_min -3`：排除跌幅超过3%的

**`--no_filter`**：默认会过滤掉创业板(300/301)、科创板(688)、北交所(9开头)的股票，加此参数保留全部。

---

## 策略一：vp_sync（量价同步）

通过滑动窗口判断量比和价格是否同步上涨。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--window` | int | 5 | 滑动窗口大小（分钟） |
| `--sync_threshold` | float | 0.25 | 同步率阈值，0~1之间 |
| `--vr_threshold` | float | 0.8 | 量比阈值，窗口内平均量比需大于此值 |

### 示例

```bash
# 默认参数
python main.py --strategy vp_sync --file codes.txt --date 20260519

# 3分钟窗口，更严格
python main.py --strategy vp_sync --file codes.txt --date 20260519 --window 3 --sync_threshold 0.3

# 盘中模拟，只看上涨0~5%
python main.py --strategy vp_sync --file codes.txt --date 20260519 --until 10:00 --change_min 0 --change_max 5
```

---

## 策略二：vp_pulse（量比脉冲）

捕捉盘中量比突然放大的脉冲点，要求量比递增且价格不跌。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--pulse` | float | 2.0 | 脉冲倍数阈值，分钟量/均量 ≥ 此值才算脉冲 |
| `--min_hits` | int | 3 | 最少脉冲点数，全天命中需 ≥ 此值 |
| `--no_price_up` | flag | 否 | 不要求脉冲点价格上涨（默认要求） |
| `--no_vol_up` | flag | 否 | 不要求量比递增，可捕捉下降沿脉冲 |
| `--merge_gap` | int | 2 | 脉冲点间隔 ≤ 此值合并为同一时段 |

### 示例

```bash
# 默认参数
python main.py --strategy vp_pulse --file codes.txt --date 20260519

# 只抓大脉冲（3倍以上）
python main.py --strategy vp_pulse --file codes.txt --date 20260519 --pulse 3.0

# 宽松模式，至少2个脉冲点
python main.py --strategy vp_pulse --file codes.txt --date 20260519 --pulse 1.5 --min_hits 2

# 不要求量比递增（含下降沿）
python main.py --strategy vp_pulse --file codes.txt --date 20260519 --no_vol_up

# 盘中模拟 + 涨幅过滤
python main.py --strategy vp_pulse --file codes.txt --date 20260519 --until 10:00 --change_min 0 --change_max 7
```

---

## 策略三：vr_slope（量比斜率）

以滑动窗口计算量比斜率角度，捕捉量比持续上升且价格上涨的时段。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--vr_slope_window` | int | 3 | 窗口大小（分钟） |
| `--vr_slope` | float | 5 | 量比斜率角度阈值（度） |
| `--no_vr_up` | flag | 否 | 不要求窗口首尾量比增加（默认要求） |
| `--no_vr_slope_price_up` | flag | 否 | 不要求窗口首尾价格上涨（默认要求） |
| `--vr_slope_min_hits` | int | 3 | 最少命中窗口数 |
| `--vr_slope_merge_gap` | int | 2 | 命中窗口间隔 ≤ 此值合并为同一时段 |

### 判断逻辑

```
窗口 [start, start+window-1]：
  ① 量比斜率角度 ≥ vr_slope → 量比上升够陡
  ② VR[end] > VR[start] → 量比确实增加（--no_vr_up 可关闭）
  ③ price[end] >= price[start] → 价格不下跌（--no_vr_slope_price_up 可关闭）
  三者同时满足 → 命中
```

### 角度对照表

| 角度 | 3分钟VR变化 | 5分钟VR变化 | 含义 |
|------|------------|------------|------|
| 3° | 2.00→2.16 | 2.00→2.26 | 温和放量 |
| 5° | 2.00→2.26 | 2.00→2.44 | 明显放量（默认） |
| 10° | 2.00→2.53 | 2.00→2.88 | 较强放量 |
| 15° | 2.00→2.80 | 2.00→3.34 | 强势放量 |
| 20° | 2.00→3.09 | 2.00→3.82 | 剧烈放量 |
| 30° | 2.00→3.73 | 2.00→4.89 | 暴量拉升 |
| 45° | 2.00→5.00 | 2.00→7.00 | 极端拉升 |

### 示例

```bash
# 默认：3分钟窗口，5度以上
python main.py --strategy vr_slope --file codes.txt --date 20260519

# 10度以上（更严格，只抓明显放量）
python main.py --strategy vr_slope --file codes.txt --date 20260519 --vr_slope 10

# 5分钟窗口，15度以上
python main.py --strategy vr_slope --file codes.txt --date 20260519 --vr_slope_window 5 --vr_slope 15

# 不要求量比增加
python main.py --strategy vr_slope --file codes.txt --date 20260519 --no_vr_up

# 不要求价格上涨
python main.py --strategy vr_slope --file codes.txt --date 20260519 --no_vr_slope_price_up

# 盘中模拟 + 涨幅0~7%
python main.py --strategy vr_slope --file codes.txt --date 20260519 --until 10:00 --change_min 0 --change_max 7

# 5分钟窗口 + 10度 + 盘中模拟 + 导出CSV
python main.py --strategy vr_slope --file codes.txt --date 20260519 --vr_slope_window 5 --vr_slope 10 --until 10:00 --csv
```

---

## 组合使用示例

```bash
# 盘中10点运行，vr_slope策略，5分钟窗口，8度以上，涨幅0~7%，导出CSV
python main.py --strategy vr_slope --file codes.txt --date 20260519 \
  --vr_slope_window 5 --vr_slope 8 \
  --until 10:00 --change_min 0 --change_max 7 --csv

# vp_pulse策略，3倍大脉冲，涨幅不超过5%
python main.py --strategy vp_pulse --file codes.txt --date 20260519 \
  --pulse 3.0 --change_max 5

# 不过滤创业板科创板，vr_slope宽松模式
python main.py --strategy vr_slope --file codes.txt --date 20260519 \
  --vr_slope 3 --no_filter
```
