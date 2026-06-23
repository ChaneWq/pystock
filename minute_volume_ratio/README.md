# 分时量比计算模块

## 量比说明

量比是衡量当日成交量相对历史平均成交量的指标，反映盘中放量/缩量程度。

**公式**（通达信）：

```
时间序号:=IF(HOUR>12,(HOUR-13)*60+MINUTE+120,(HOUR-9)*60+MINUTE-30)+1;
量比:=SUM(V,0)/时间序号/DYNAINFO(16);
```

即：**量比 = 当日分钟均量 / 过去5日分钟均量**

| 量比范围 | 含义 |
|----------|------|
| > 3      | 明显放量 |
| 2 ~ 3    | 放量 |
| 1 ~ 2    | 正常 |
| 0.5 ~ 1  | 缩量 |
| < 0.5    | 明显缩量 |

## 必须数据

| 数据项 | 说明 | 来源 |
|--------|------|------|
| 当日分时数据 | 每分钟成交量 + 时间 | `client.minutes()` |
| 过去5日日线数据 | 每天总成交量 | `client.bars(frequency='day')` |

## 文件结构

```
minute_volume_ratio/
├── minute_vr_fetcher.py  # 数据获取层：分时数据 + 日线数据
├── minute_vr_calc.py     # 计算层：时间序号 + 量比（纯计算，不依赖数据源）
└── minute_vr_cli.py      # 命令行入口：参数解析 + 结果输出
```

## 使用方式

### 单股指定日期

```bash
python minute_vr_cli.py --code 000400 --date 20260420
```

### 单股当天（盘中实时）

```bash
python minute_vr_cli.py --code 000400
```

### 导出CSV

```bash
python minute_vr_cli.py --code 000400 --date 20260420 --csv
```

CSV 文件输出到当前目录，命名格式：`{code}_{date}_vr.csv`

### 批量计算

从文本文件读取股票列表，每行一个代码：

```bash
python minute_vr_cli.py --file stock_codes.txt --date 20260420
```

### 自定义历史天数

默认取过去5个交易日，可通过 `--n` 参数调整：

```bash
python minute_vr_cli.py --code 000400 --date 20260420 --n 10
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--code` | 与 `--file` 二选一 | 股票代码，如 000400 |
| `--date` | 否 | 日期，格式 YYYYMMDD，默认当天 |
| `--n` | 否 | 过去n个交易日，默认5 |
| `--file` | 与 `--code` 二选一 | 股票代码文件路径 |
| `--csv` | 否 | 是否导出CSV文件 |

## 输出示例

```
股票: 000400  日期: 2026-04-20  5日分钟均量: 1340
--------------------------------------------------------------------------------
时间       序号      累计量      量比
--------------------------------------------------------------------------------
09:30         1        87800      5.76
09:31         2       185400      6.09
09:32         3       260400      5.70
...
14:59       240     42403200      1.32
--------------------------------------------------------------------------------
```

## 代码调用

也可以在其他 Python 代码中直接调用：

### 基础计算

```python
from minute_vr_fetcher import get_minute_data, get_prev_n_day_vol
from minute_vr_calc import calc_avg_vol_per_minute, calc_volume_ratio
from day_index import init_create_client

client = init_create_client()

# 获取数据
minute_df = get_minute_data('000400', '20260420', client)
day_vol_list = get_prev_n_day_vol('000400', 5, client)

# 计算量比
avg_vol = calc_avg_vol_per_minute(day_vol_list, 5)
result_df = calc_volume_ratio(minute_df, avg_vol)

# result_df 包含列: price, vol, hour, minute, trade_date, time_index, cumulative_vol, volume_ratio
```

### 查询接口

```python
from minute_vr_calc import get_volume_ratio_at_time, get_volume_ratio_range, get_current_volume_ratio

# 获取指定时间点的量比
vr_1030 = get_volume_ratio_at_time(result_df, hour=10, minute=30)
# 返回: 1.85

# 获取时间段量比
morning_vr = get_volume_ratio_range(result_df, start_time='09:30', end_time='11:30')
# 返回: DataFrame（上午时段数据）

# 获取最新量比
latest_vr = get_current_volume_ratio(result_df)
# 返回: 1.32
```

### 统计接口

```python
from minute_vr_calc import get_volume_ratio_summary, get_volume_ratio_trend

# 获取量比统计摘要
summary = get_volume_ratio_summary(result_df)
# 返回: {'max': 6.09, 'min': 0.85, 'avg': 1.56, 'current': 1.32}

# 判断量比趋势
trend = get_volume_ratio_trend(result_df, window=10)
# 返回: '上升' / '下降' / '平稳'
```

### 过滤接口

```python
from minute_vr_calc import filter_volume_ratio_by_range, find_volume_ratio_peaks, find_volume_ratio_breakout

# 按量比范围过滤
high_vr_df = filter_volume_ratio_by_range(result_df, min_vr=2.0)
# 返回: 量比 >= 2.0 的时段

# 查找量比峰值时段
peaks = find_volume_ratio_peaks(result_df, threshold=3.0)
# 返回: [('09:31', 6.09), ('10:15', 3.85)]

# 查找量比突破时段
breakouts = find_volume_ratio_breakout(result_df, threshold=2.0)
# 返回: [('09:45', 1.2, 2.5), ('10:30', 1.5, 2.8)]
```

### 比较接口

```python
from minute_vr_cli import calc_stock_minute_vr, compare_volume_ratio_stocks, compare_volume_ratio_days

# 计算单股票量比（返回DataFrame）
df = calc_stock_minute_vr('000400', '20260420')

# 多股票量比对比
compare_df = compare_volume_ratio_stocks(['000400', '000001'], '20260420')
# 返回: DataFrame（各股票量比对比）

# 多日量比对比
days_df = compare_volume_ratio_days('000400', ['20260418', '20260419', '20260420'])
# 返回: DataFrame（多日量比趋势）
```

## 接口列表

| 模块 | 函数 | 用途 |
|------|------|------|
| `minute_vr_calc.py` | `calc_time_index` | 计算时间序号 |
| `minute_vr_calc.py` | `calc_avg_vol_per_minute` | 计算分钟均量 |
| `minute_vr_calc.py` | `calc_volume_ratio` | 计算量比DataFrame |
| `minute_vr_calc.py` | `get_volume_ratio_at_time` | 获取指定时间点量比 |
| `minute_vr_calc.py` | `get_volume_ratio_range` | 获取时间段量比 |
| `minute_vr_calc.py` | `get_current_volume_ratio` | 获取最新量比 |
| `minute_vr_calc.py` | `get_volume_ratio_summary` | 获取量比统计摘要 |
| `minute_vr_calc.py` | `get_volume_ratio_trend` | 判断量比趋势 |
| `minute_vr_calc.py` | `filter_volume_ratio_by_range` | 按量比范围过滤 |
| `minute_vr_calc.py` | `find_volume_ratio_peaks` | 查找量比峰值时段 |
| `minute_vr_calc.py` | `find_volume_ratio_breakout` | 查找量比突破时段 |
| `minute_vr_cli.py` | `calc_stock_minute_vr` | 计算单股票量比 |
| `minute_vr_cli.py` | `iter_stocks_minute_vr` | 迭代计算多股票量比 |
| `minute_vr_cli.py` | `print_stock_minute_vr` | 打印单股票量比 |
| `minute_vr_cli.py` | `print_stocks_minute_vr` | 打印批量股票量比 |
| `minute_vr_cli.py` | `compare_volume_ratio_stocks` | 多股票量比对比 |
| `minute_vr_cli.py` | `compare_volume_ratio_days` | 多日量比对比 |

## 依赖

- `mootdx` - 通达信数据接口
- `pandas`
- `numpy`
