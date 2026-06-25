import pandas as pd
import numpy as np
import requests
import json
from mootdx.quotes import Quotes

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment

def init_create_client():
    client = Quotes.factory(market='std')
    return client


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
        "日均成交量": int(total_volume / len(period_df))
    }

    return result


def process_stocks_from_excel(client, input_file, output_file, date_str, n_days):
    """
    从Excel读取股票列表，计算每只股票的表现，并输出到新Excel文件

    参数:
    client: 初始化后的客户端对象
    input_file: 输入Excel文件路径
    output_file: 输出Excel文件路径
    date_str: 起始日期(格式为'YYYY-MM-DD')
    n_days: 交易日天数(整数)
    """
    # 读取输入Excel文件
    try:
        input_df = pd.read_excel(input_file)
        # input_df = pd.read_excel(input_excel, engine='xlrd')

    except Exception as e:
        print(f"读取输入文件失败: {e}")
        raise
        return

    # 检查必要的列是否存在
    if '代码' not in input_df.columns:
        print("输入文件中缺少'代码'列")
        return

    # 创建输出Excel文件
    wb = Workbook()
    ws = wb.active
    ws.title = "股票表现汇总"

    # 写入表头
    headers = [
        "股票代码", "股票名称", "起始日期", "结束日期", "交易日天数",
        "起始价", "结束价", "总涨幅(%)", "最高价", "最低价", "平均价",
        "平均日涨幅(%)", "最大单日涨幅(%)", "最大单日跌幅(%)",
        "上涨天数", "下跌天数", "总成交量", "日均成交量", "错误信息"
    ]
    ws.append(headers)

    # 设置表头样式
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # 处理每只股票
    for _, row in input_df.iterrows():
        code = str(row['代码']).zfill(6)  # 确保股票代码是6位
        name = row.get('名称(272)', '')

        try:
            # 获取股票表现数据
            performance = get_stock_performance(client, code, date_str, n_days)

            if "error" in performance:
                # 如果有错误，只写入错误信息
                ws.append([
                    code, name, "", "", "", "", "", "", "", "",
                    "", "", "", "", "", "", "", "", performance["error"]
                ])
            else:
                # 写入完整数据
                ws.append([
                    performance["股票代码"],
                    name,
                    performance["起始日期"],
                    performance["结束日期"],
                    performance["交易日天数"],
                    performance["起始价"],
                    performance["结束价"],
                    performance["总涨幅(%)"],
                    performance["最高价"],
                    performance["最低价"],
                    performance["平均价"],
                    performance["平均日涨幅(%)"],
                    performance["最大单日涨幅(%)"],
                    performance["最大单日跌幅(%)"],
                    performance["上涨天数"],
                    performance["下跌天数"],
                    performance["总成交量"],
                    performance["日均成交量"],
                    ""
                ])
        except Exception as e:
            ws.append([
                code, name, "", "", "", "", "", "", "", "",
                "", "", "", "", "", "", "", "", f"处理失败: {str(e)}"
            ])

        # 自动调整列宽
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[column_letter].width = adjusted_width

    # 保存输出文件
    try:
        wb.save(output_file)
        print(f"结果已保存到: {output_file}")
    except Exception as e:
        print(f"保存输出文件失败: {e}")
        raise


# 使用示例
if __name__ == "__main__":
    client = init_create_client()  # 假设已经初始化了客户端

    # 输入参数
    input_excel = "临时条件股20250830.xls.xlsx"
    output_excel = "股票表现分析结果.xlsx"
    start_date = "2025-08-26"  # 起始日期
    trading_days = 2  # 分析后5个交易日的表现

    # 处理股票并输出结果
    process_stocks_from_excel(client, input_excel, output_excel, start_date, trading_days)