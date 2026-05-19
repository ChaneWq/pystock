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
├── fetcher.py      # 数据获取层：分时数据 + 日线数据
├── calculator.py   # 计算层：时间序号 + 量比（纯计算，不依赖数据源）
└── main.py         # 入口：命令行参数解析 + 结果输出
```

## 使用方式

### 单股指定日期

```bash
python main.py --code 000400 --date 20260420
```

### 单股当天（盘中实时）

```bash
python main.py --code 000400
```

### 导出CSV

```bash
python main.py --code 000400 --date 20260420 --csv
```

CSV 文件输出到当前目录，命名格式：`{code}_{date}_vr.csv`

### 批量计算

从文本文件读取股票列表，每行一个代码：

```bash
python main.py --file stock_codes.txt --date 20260420
```

### 自定义历史天数

默认取过去5个交易日，可通过 `--n` 参数调整：

```bash
python main.py --code 000400 --date 20260420 --n 10
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

```python
from fetcher import get_minute_data, get_prev_n_day_vol
from calculator import calc_avg_vol_per_minute, calc_volume_ratio
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

## 依赖

- `mootdx` - 通达信数据接口
- `pandas`
- `numpy`
