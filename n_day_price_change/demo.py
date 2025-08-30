import pandas as pd
import numpy as np
import requests
import json
from mootdx.quotes import Quotes

def init_create_client():
    client = Quotes.factory(market='std')
    return client


import pandas as pd

def get_stock_performance(client, code, date_str, n_days):
    """
    获取指定股票在特定日期后n个交易日的表现汇总

    参数:
    client: 初始化后的客户端对象
    code: 股票代码(字符串)
    date_str: 起始日期(格式为'YYYY-MM-DD')
    n_days: 交易日天数(整数)

    返回:
    dict包含n个交易日内各项指标的汇总

    特定日期当天开始的收盘，到第（特定日期+n-1）交易日日期的收盘价
    n_days 是包括特定日期当天的
    """
    # 获取足够多的历史数据以确保包含所需日期范围
    df = client.bars(symbol=code, frequency='day', offset=300)

    # 确保datetime列是datetime类型
    df['datetime'] = pd.to_datetime(df['datetime'])

    # 重置索引并排序（解决datetime同时作为索引和列的问题）
    df = df.reset_index(drop=True).sort_values('datetime')

    # 将输入日期转换为datetime对象
    start_date = pd.to_datetime(date_str)

    # 找到起始日期在数据中的位置
    mask = df['datetime'] >= start_date
    if not mask.any():
        return {"error": "起始日期不在数据范围内"}

    start_idx = df[mask].index[0]

    # 获取从起始日期开始的n个交易日
    period_df = df.iloc[start_idx:start_idx + n_days].copy()

    if len(period_df) < n_days:
        return {"error": f"数据不足，只有{len(period_df)}个交易日数据"}

    # 计算各项指标
    start_price = period_df.iloc[0]['close']
    end_price = period_df.iloc[-1]['close']
    highest_price = period_df['high'].max()
    lowest_price = period_df['low'].min()
    average_price = period_df['close'].mean()
    total_volume = period_df['volume'].sum()

    # 计算涨幅(百分比)
    price_change = (end_price - start_price) / start_price * 100

    # 计算每日涨跌幅
    daily_changes = period_df['close'].pct_change().dropna() * 100
    avg_daily_change = daily_changes.mean()
    max_daily_gain = daily_changes.max()
    max_daily_loss = daily_changes.min()

    # 计算上涨天数和下跌天数
    up_days = (daily_changes > 0).sum()
    down_days = (daily_changes < 0).sum()

    # 汇总结果
    result = {
        "股票代码": code,
        "起始日期": period_df.iloc[0]['datetime'].strftime('%Y-%m-%d'),
        "结束日期": period_df.iloc[-1]['datetime'].strftime('%Y-%m-%d'),
        "交易日天数": len(period_df),
        "起始价": round(start_price, 2),
        "结束价": round(end_price, 2),
        "最高价": round(highest_price, 2),
        "最低价": round(lowest_price, 2),
        "平均价": round(average_price, 2),
        "总涨幅(%)": round(price_change, 2),
        "平均日涨幅(%)": round(avg_daily_change, 2),
        "最大单日涨幅(%)": round(max_daily_gain, 2),
        "最大单日跌幅(%)": round(max_daily_loss, 2),
        "上涨天数": up_days,
        "下跌天数": down_days,
        "总成交量": int(total_volume),
        "日均成交量": int(total_volume / len(period_df)),
        "详细数据": period_df[['datetime', 'open', 'close', 'high', 'low', 'volume']].to_dict('records')
    }

    return result


# 使用示例
if __name__ == "__main__":
    client = init_create_client()  # 假设已经初始化了客户端
    code = '002544'
    date_str = '2025-08-21'
    trading_days = 4  # 获取后5个交易日的数据

    performance = get_stock_performance(client, code, date_str, trading_days)

    if "error" in performance:
        print(f"错误: {performance['error']}")
    else:
        # 打印汇总结果
        print(f"股票代码: {performance['股票代码']}")
        print(f"时间段: {performance['起始日期']} 至 {performance['结束日期']} ({performance['交易日天数']}个交易日)")
        print(f"起始价: {performance['起始价']}, 结束价: {performance['结束价']}")
        print(f"总涨幅: {performance['总涨幅(%)']}%")
        print(f"最高价: {performance['最高价']}, 最低价: {performance['最低价']}")
        print(f"平均价: {performance['平均价']}")
        print(f"平均日涨幅: {performance['平均日涨幅(%)']}%")
        print(f"最大单日涨幅: {performance['最大单日涨幅(%)']}%, 最大单日跌幅: {performance['最大单日跌幅(%)']}%")
        print(f"上涨天数: {performance['上涨天数']}, 下跌天数: {performance['下跌天数']}")
        print(f"总成交量: {performance['总成交量']}, 日均成交量: {performance['日均成交量']}")

        # 如果需要查看详细数据
        print("\n详细数据:")
        for day in performance['详细数据']:
            print(f"{day['datetime'].strftime('%Y-%m-%d')}: 开盘{day['open']}, 收盘{day['close']}, 最高{day['high']}, 最低{day['low']}, 成交量{day['volume']}")