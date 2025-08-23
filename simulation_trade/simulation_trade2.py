import matplotlib.pyplot as plt
import tdx_indicator
from mootdx.quotes import Quotes
plt.rcParams['font.sans-serif']=['SimHei']#显示中文标签
plt.rcParams['axes.unicode_minus']=False


def init_create_client():
    client = Quotes.factory(market='std')
    return client

def get_day_macd(code, datestr="", client="",days=100):
    # 获取最近300日东方财富K线数据
    df = client.bars(symbol=code, frequency='day', offset=days)
    if df is None or df.empty:
        print("数据为空")
        return 0, 0, 0
    
    # 设置自定义整数索引
    custom_index = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
    df.set_index(custom_index, inplace=True)
    
    # 处理退市或无收盘价数据情况
    try:
        close = df['close']
        high = df['high']
        low = df['low']
    except KeyError:
        print("缺少'close'列，可能是退市股票或数据异常")
        return 0, 0, 0
  
    # 计算MACD指标
    DIF, DEA, MACD = tdx_indicator.MACD(close)
    K, D, J = tdx_indicator.KDJ(close, high, low)
    BBI = tdx_indicator.BBI(close)
    ma = tdx_indicator.MA(close, 250)
    ma60 = tdx_indicator.MA(close, 250)
    # 将MACD指标添加为DataFrame新列
 
    df['DIF'] = DIF
    df['DEA'] = DEA
    df['MACD'] = MACD
    df['K'] = K
    df['D'] = D
    df['J'] = J
    df['BBI'] = BBI
    df['MA250'] = ma
    df['MA60'] = ma60
    df = df.round({'DIF': 2, 'DEA': 2, 'MACD': 2, 'K': 2, 'D': 2, 'J': 2, 'BBI': 2,'MA250': 2,'MA60': 2})
    df = df.drop(df.index[:23])  # 删除前23行（索引从0开始）
    df['datetime'] = pd.to_datetime(df['datetime'])
 
    
    # print(df)
    # print(df.columns)
    
    # df.to_csv('gegu_result.csv',index=False)
 
    
    return df
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 主回测函数，支持凯利动态仓位 ---
def backtest_common_logic(df, initial_cash, strategy_name, buy_condition):
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)

    cash = initial_cash
    stock_qty = 0
    holding = False
    half_exit_flag = False
    buy_day_low = 0
    buy_price = 0
    trade_log = []
    equity_curve = []

    below_bbi_count = 0
    trade_id = 0
    current_trade = None

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1]
        today_value = cash + stock_qty * row['close']
        equity_curve.append({'datetime': row['datetime'], 'value': today_value})

        # 止损
        if holding and row['close'] < buy_day_low * 0.99:
            cash += stock_qty * row['close']
            stock_qty = 0
            current_trade['操作'].append((row['datetime'], '止损清仓', row['close']))
            current_trade['卖出价'] = row['close']
            current_trade['收益率'] = round((row['close'] - buy_price) / buy_price * 100, 2)
            current_trade['持股天数'] = (row['datetime'] - current_trade['买入时间']).days
            trade_log.append(current_trade)
            holding = False
            half_exit_flag = False
            below_bbi_count = 0
            current_trade = None
            continue

        # 清仓逻辑
        if half_exit_flag:
            if row['close'] < row['BBI']:
                below_bbi_count += 1
            else:
                below_bbi_count = 0
            if below_bbi_count >= 2:
                cash += stock_qty * row['close']
                stock_qty = 0
                current_trade['操作'].append((row['datetime'], '清仓', row['close']))
                current_trade['卖出价'] = row['close']
                current_trade['收益率'] += round((row['close'] - buy_price) / buy_price * 0.5 * 100, 2)
                current_trade['持股天数'] = (row['datetime'] - current_trade['买入时间']).days
                trade_log.append(current_trade)
                holding = False
                half_exit_flag = False
                below_bbi_count = 0
                current_trade = None
                continue

        # 减仓
        if holding and not half_exit_flag:
            price_change = (row['close'] - prev_row['close']) / prev_row['close']
            if row['close'] > row['BBI'] and price_change >= 0.05:
                sell_qty = stock_qty * 0.5
                cash += sell_qty * row['close']
                stock_qty -= sell_qty
                half_exit_flag = True
                below_bbi_count = 0
                current_trade['操作'].append((row['datetime'], '减仓一半', row['close']))
                current_trade['收益率'] = round((row['close'] - buy_price) / buy_price * 0.5 * 100, 2)
                continue

        # 买入
        if not holding and buy_condition(row):
            buy_day_low = row['low']
            buy_price = row['close']
            holding = True
            half_exit_flag = False
            below_bbi_count = 0

            # 动态仓位（凯利公式计算）
            win_trades = [t for t in trade_log if t['收益率'] > 0]
            loss_trades = [t for t in trade_log if t['收益率'] < 0]
            W = len(win_trades) / len(trade_log) if trade_log else 0.5
            R = (np.mean([t['收益率'] for t in win_trades]) / abs(np.mean([t['收益率'] for t in loss_trades]))
                 if loss_trades else 2)
            kelly = W - (1 - W) / R if R > 0 else 0.1
            kelly = max(min(kelly, 1), 0.1)  # 限定在10%-100%仓位

            position_cash = cash * kelly
            stock_qty = int(position_cash // row['close'])
            cash -= stock_qty * row['close']

            current_trade = {
                '策略': strategy_name,
                '收益率': 0.0,
                '交易编号': trade_id,
                '买入时间': row['datetime'],
                '买入价': row['close'],
                '卖出价': None,
                '持股天数': None,
                '操作': [(row['datetime'], '买入', row['close'])],
                '凯利仓位比例': round(kelly, 2)
            }
            trade_id += 1
            continue

    # 强制结算
    last_row = df.iloc[-1]
    if holding:
        current_trade['操作'].append((last_row['datetime'], '强制结算', last_row['close']))
        if half_exit_flag:
            current_trade['收益率'] += round((last_row['close'] - buy_price) / buy_price * 0.5 * 100, 2)
        else:
            current_trade['收益率'] = round((last_row['close'] - buy_price) / buy_price * 100, 2)
        current_trade['卖出价'] = last_row['close']
        current_trade['持股天数'] = (last_row['datetime'] - current_trade['买入时间']).days
        trade_log.append(current_trade)
        cash += stock_qty * last_row['close']

    # 回测曲线
    equity_df = pd.DataFrame(equity_curve).set_index('datetime')
    equity_df['returns'] = equity_df['value'].pct_change()
    equity_df['cumulative'] = equity_df['value'] / initial_cash
    max_drawdown = (equity_df['cumulative'].cummax() - equity_df['cumulative']).max()
    annual_return = (equity_df['cumulative'].iloc[-1]) ** (250 / len(equity_df)) - 1

    # 盈亏统计
    wins = [t['收益率'] for t in trade_log if t['收益率'] > 0]
    losses = [t['收益率'] for t in trade_log if t['收益率'] < 0]
    W = len(wins) / len(trade_log) if trade_log else 0
    R = np.mean(wins) / abs(np.mean(losses)) if losses else np.inf
    kelly = W - (1 - W) / R if R > 0 else 0.1
    kelly = max(min(kelly, 1), 0.1)

    total_days = sum(t['持股天数'] for t in trade_log)

    metrics = {
        '策略': strategy_name,
        '最终资金': float(round(equity_df['value'].iloc[-1], 2)),
        '总收益率': float(round((equity_df['value'].iloc[-1] - initial_cash) / initial_cash * 100, 2)),
        '最大回撤': float(round(max_drawdown * 100, 2)),
        '年化收益率': float(round(annual_return * 100, 2)),
        '总持股天数': int(total_days),
        '胜率': float(round(W * 100, 2)),
        '盈亏比': float(round(R, 2)),
        '凯利建议仓位': float(round(kelly * 100, 2))
    }

    return trade_log, equity_df, metrics


# --- 策略1 ---
def backtest_strategy_j_dif(df, initial_cash=30000):
    return backtest_common_logic(df, initial_cash, "策略1_J_DIF", lambda row: row['J'] < 5 and row['DIF'] > 0)

# --- 策略2 ---
def backtest_strategy_j_only(df, initial_cash=30000):
    return backtest_common_logic(df, initial_cash, "策略2_J", lambda row: row['J'] < 5)

# --- 策略3 ---
def backtest_strategy_j_ma(df, initial_cash=30000):
    return backtest_common_logic(df, initial_cash, "策略3_J_MA", lambda row: row['J'] < 5 and row['MA250'] < row['close'])

# --- 策略4 ---
def backtest_strategy_j_ma_dif(df, initial_cash=30000):
    return backtest_common_logic(df, initial_cash, "策略3_J_MA", lambda row: row['J'] < 5 and row['MA60'] > row['close'])

# --- 绘图 ---
def plot_two_equity_curves(eq1, eq2, label1='策略1', label2='策略2'):
    plt.figure(figsize=(12, 6))
    plt.plot(eq1.index, eq1['value'], label=label1 + ' 资金曲线', linewidth=2)
    plt.plot(eq2.index, eq2['value'], label=label2 + ' 资金曲线', linewidth=2)
    plt.title("资金曲线对比")
    plt.xlabel("日期")
    plt.ylabel("资产价值")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_yield_curve(eq1, eq2, label1='策略1', label2='策略2'):
    plt.figure(figsize=(12, 6))
    plt.plot(eq1.index, eq1['cumulative'] * 100 - 100, label=label1 + ' 收益率', linestyle='--')
    plt.plot(eq2.index, eq2['cumulative'] * 100 - 100, label=label2 + ' 收益率', linestyle='--')
    plt.title("收益率曲线对比")
    plt.xlabel("日期")
    plt.ylabel("累计收益率（%）")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# --- 主函数入口 ---
if __name__ == "__main__":
    # df = pd.read_csv("your_data.csv")  # 替换为你的文件路径
    # 数据加载：将你的CSV文件路径替换下面
    # df = pd.read_csv("your_data.csv")
    client = init_create_client()
    days = 100000
    df = get_day_macd("000400", "2025-06-12", client, days)
    print(df)
    log1, eq1, m1 = backtest_strategy_j_dif(df)
    log2, eq2, m2 = backtest_strategy_j_only(df)
    log3, eq3, m3 = backtest_strategy_j_ma(df)
    log4, eq4, m4 = backtest_strategy_j_ma_dif(df)

    print("策略1绩效：", m1)
    print("策略2绩效：", m2)
    print("策略3绩效：", m3)
    print("策略3绩效：", m4)

    plt.figure(figsize=(12, 6))
    plt.plot(eq1.index, eq1['value'], label= ' j_diff', linewidth=2)
    # plt.plot(eq2.index, eq2['value'], label= ' j', linewidth=2)
    plt.plot(eq3.index, eq3['value'], label= ' j_ma', linewidth=2)
    plt.plot(eq4.index, eq4['value'], label= ' j_ma60', linewidth=2)
    plt.title("资金曲线对比")
    plt.xlabel("日期")
    plt.ylabel("资产价值")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # plot_two_equity_curves(eq1, eq2, label1="策略1_J_DIF", label2="策略2_J")
    # plot_yield_curve(eq1, eq2, label1="策略1_J_DIF", label2="策略2_J")

    pd.DataFrame(log1).to_csv("策略1_交易记录.csv", index=False)
    pd.DataFrame(log2).to_csv("策略2_交易记录.csv", index=False)
