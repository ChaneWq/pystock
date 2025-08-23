
import pandas as pd
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
	
	# 将MACD指标添加为DataFrame新列
	df['DIF'] = DIF
	df['DEA'] = DEA
	df['MACD'] = MACD
	df['K'] = K
	df['D'] = D
	df['J'] = J
	df['BBI'] = BBI
	df = df.round({'DIF': 2, 'DEA': 2, 'MACD': 2, 'K': 2, 'D': 2, 'J': 2, 'BBI': 2})
	df = df.drop(df.index[:23])  # 删除前23行（索引从0开始）
	df['datetime'] = pd.to_datetime(df['datetime'])
	
	# print(df)
	# print(df.columns)
	
	# df.to_csv('gegu_result.csv',index=False)
	
	return df

# --- 回测策略通用逻辑 ---
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

        # 止损条件
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

        # 清仓逻辑：已减仓后，连续两日低于BBI
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

        # 减仓逻辑
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

        # 买入逻辑
        if not holding and buy_condition(row):
            buy_day_low = row['low']
            buy_price = row['close']
            holding = True
            half_exit_flag = False
            below_bbi_count = 0
            stock_qty = int(cash // row['close'])
            cash -= stock_qty * row['close']
            current_trade = {
                '策略': strategy_name,
                '交易编号': trade_id,
                '买入时间': row['datetime'],
                '买入价': row['close'],
                '卖出价': None,
                '收益率': 0.0,
                '持股天数': None,
                '操作': [(row['datetime'], '买入', row['close'])]
            }
            trade_id += 1
            continue

    # 最后强制结算
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
        stock_qty = 0

    # 回测指标与资金曲线
    equity_df = pd.DataFrame(equity_curve).set_index('datetime')
    equity_df['returns'] = equity_df['value'].pct_change()
    equity_df['cumulative'] = equity_df['value'] / initial_cash
    max_drawdown = (equity_df['cumulative'].cummax() - equity_df['cumulative']).max()
    annual_return = (equity_df['cumulative'].iloc[-1]) ** (250 / len(equity_df)) - 1

    metrics = {
        '策略': strategy_name,
        '最终资金': round(equity_df['value'].iloc[-1], 2),
        '总收益率': round((equity_df['value'].iloc[-1] - initial_cash) / initial_cash * 100, 2),
        '最大回撤': round(max_drawdown * 100, 2),
        '年化收益率': round(annual_return * 100, 2)
    }

    return trade_log, equity_df, metrics

# --- 策略1 ---
def backtest_strategy_j_dif(df, initial_cash=30000):
    return backtest_common_logic(df, initial_cash, "策略1_J_DIF", lambda row: row['J'] < 0 and row['DIF'] > 0)

# --- 策略2 ---
def backtest_strategy_j_only(df, initial_cash=30000):
    return backtest_common_logic(df, initial_cash, "策略2_J", lambda row: row['J'] < 0)

# --- 绘图 ---
def plot_two_equity_curves(eq1, eq2, label1='策略1', label2='策略2'):
    plt.figure(figsize=(12, 6))
    plt.plot(eq1.index, eq1['value'], label=label1, color='blue')
    plt.plot(eq2.index, eq2['value'], label=label2, color='green')
    plt.title("策略资金曲线对比")
    plt.xlabel("时间")
    plt.ylabel("资产价值")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- 主程序入口 ---
if __name__ == "__main__":
    # 数据加载：将你的CSV文件路径替换下面
    # df = pd.read_csv("your_data.csv")
    client = init_create_client()
    days = 200
    df = get_day_macd("601555", "2025-06-12", client,days)

    # 策略1回测
    log1, eq1, m1 = backtest_strategy_j_dif(df)

    # 策略2回测
    log2, eq2, m2 = backtest_strategy_j_only(df)

    # 绘图对比
    plot_two_equity_curves(eq1, eq2, label1="策略1_J_DIF", label2="策略2_J")

    # 可选：查看交易明细
    trade_df1 = pd.DataFrame(log1)
    trade_df2 = pd.DataFrame(log2)
    trade_df1.to_csv("策略1_交易记录.csv", index=False)
    trade_df2.to_csv("策略2_交易记录.csv", index=False)
    
    
    print("策略1结果：", m1)
    print("策略2结果：", m2)
    
    
