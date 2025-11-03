import requests
import json
from mootdx.quotes import Quotes
import pandas as pd
# import stock.tdx_indicator as tdx_indicator
import tdx_indicator as tdx_indicator

def init_create_client():
    """
    初始化client，用于传入后续的方法
    """
    client = Quotes.factory(market='std')
    return client


def get_cur_price(code, client=""):
    """
    获取指定股票的最新价格
    
    参数:
    code: 股票代码
    client: 数据客户端
    
    返回:
    float: 股票最新价格
    """
    # 获取最近1日的K线数据
    df = client.bars(symbol=code, frequency='day', offset=1)
    
    if df is not None and not df.empty:
        # 返回最新收盘价
        return df['close'].iloc[-1]
    else:
        # 如果没有数据，返回0
        return 0


def get_cur_data(code, client=""):
    """
    获取指定股票的最新数据
    调用示例：
    open,close,high,low,vol,amount,year,month,day,hour,minute,datetime,volume = get_cur_data('000400',client)

    参数:
    code: 股票代码
    client: 数据客户端

    返回:
    pandas.Series: 股票最新数据行，包含open, close, high, low, vol, amount等字段
    """
    # 获取最近1日的K线数据
    df = client.bars(symbol=code, frequency='day', offset=1)
    
    if df is not None and not df.empty:
        # 返回最新数据行
        return df.iloc[-1]
    else:
        # 如果没有数据，返回空的Series
        return pd.Series(dtype='object')
    
    
"""
datestr = 2025-01-09
获取最新月kdj 或 指定日期的kdj
"""
def get_month_kdj(code,datestr="",client=""):
    # client = Quotes.factory(market='std')
    # 生成自定义的整数索引列
    df = client.bars(symbol=code, frequency='mon', offset=300)  # 获取最近300日东方财富k线
    custom_index = pd.RangeIndex(start=1, stop=len(df)+1, step=1)
    # 使用自定义的整数索引列作为索引
    df.set_index(custom_index, inplace=True)
    try:
        close = df['close']
        high = df['high']
        low = df['low']
    except:
        # 如果是退市股票，直接返回0
        return (0,0,0)
    K, D, J = tdx_indicator.KDJ(close, high, low)
    if(datestr==""):
        return K[-1],D[-1],J[-1]
    else:
        try:
            index = df[df['datetime'].str.contains(datestr)].index-1
            return K[index][0],D[index][0],J[index][0]
        except:
            print("datestr格式不合规 或 该日期没有交易日 或 指定交易日错误")


"""
datestr = 2025-01-09
获取最新周kdj 或 指定日期的kdj
"""
def get_week_kdj(code,datestr="",client=""):
    # client = Quotes.factory(market='std')
    # 生成自定义的整数索引列
    
    df = client.bars(symbol=code, frequency='week', offset=300)  # 获取最近300日东方财富k线
    custom_index = pd.RangeIndex(start=1, stop=len(df)+1, step=1)
    # 使用自定义的整数索引列作为索引
    df.set_index(custom_index, inplace=True)
    try:
        close = df['close']
        high = df['high']
        low = df['low']
    except:
        # 如果是退市股票，直接返回0
        return (0,0,0)
    K, D, J = tdx_indicator.KDJ(close, high, low)
    if(datestr==""):
        # print(J[-1])
        return K[-1],D[-1],J[-1]
    else:
        try:
            index = df[df['datetime'].str.contains(datestr)].index-1
            # print(J[index])
            return K[index][0],D[index][0],J[index][0]
        except:
            print("datestr格式不合规 或 该日期没有交易日 或 指定交易日错误")



"""
datestr = 2025-01-09
获取最新日kdj 或 指定日期的kdj
"""

def get_day_kdj(code,datestr="",client=""):
    # client = Quotes.factory(market='std')
    # 生成自定义的整数索引列
    df = client.bars(symbol=code, frequency='day', offset=300)  # 获取最近300日东方财富k线
    custom_index = pd.RangeIndex(start=1, stop=len(df)+1, step=1)
    # 使用自定义的整数索引列作为索引
    df.set_index(custom_index, inplace=True)
    try:
        close = df['close']
        high = df['high']
        low = df['low']
    except:
        # 如果是退市股票，直接返回0
        return (0,0,0)
    K, D, J = tdx_indicator.KDJ(close, high, low)
    if(datestr==""):
        # print(J[-1])
        return K[-1],D[-1],J[-1]
    else:
        try:
            index = df[df['datetime'].str.contains(datestr)].index-1
            # print(J[index])
            return K[index][0],D[index][0],J[index][0]
        except:
            print("datestr格式不合规 或 该日期没有交易日 或 指定交易日错误")

"""
已废弃，接口需要充值，已更新自己的公式api
"""
def get_week_kdj_api_back(code,date_str,client=""):
    # date_str="2024-12-18"
    # code = "600004"
    url = "https://stockapi.com.cn/v1/quota/kdj?calculationCycle=101&code={}&cycle=9&cycle1=3&cycle2=3&date={}&vipCycleFlag=0".format(code,date_str)
    parsed_data = json.loads(requests.get(url).text)
    k = parsed_data['data']['k'][0]
    d = parsed_data['data']['d'][0]
    j = parsed_data['data']['j'][0]
    return k,d,j

"""
已废弃，接口需要充值，已更新自己的公式api
"""
def get_day_kdj_api_back(code,date_str):
    # date_str="2024-12-18"
    # code = "600004"
    url = "https://stockapi.com.cn/v1/quota/kdj?calculationCycle=100&code={}&cycle=9&cycle1=3&cycle2=3&date={}&vipCycleFlag=0".format(code,date_str)
    parsed_data = json.loads(requests.get(url).text)
    k = parsed_data['data']['k'][0]
    d = parsed_data['data']['d'][0]
    j = parsed_data['data']['j'][0]
    return k,d,j

def get_day_macd(code,datestr="",client=""):
    # client = Quotes.factory(market='std')
    # 生成自定义的整数索引列
    df = client.bars(symbol=code, frequency='day', offset=300)  # 获取最近300日东方财富k线
    custom_index = pd.RangeIndex(start=1, stop=len(df)+1, step=1)
    # 使用自定义的整数索引列作为索引
    df.set_index(custom_index, inplace=True)
    try:
        close = df['close']
    except:
        # 如果是退市股票，直接返回0
        return (0,0,0)
    DIF,DEA,MACD = tdx_indicator.MACD(close)
    if(datestr==""):
        # print(J[-1])
        return DIF[-1],DEA[-1],MACD[-1]
    else:
        try:
            index = df[df['datetime'].str.contains(datestr)].index-1
            # print(index)
            # print(J[index])
            return DIF[index][0],DEA[index][0],MACD[index][0]
        except:
            print("datestr格式不合规 或 该日期没有交易日 或 指定交易日错误")

def get_day_bbi(code,datestr="",client=""):
    # client = Quotes.factory(market='std')
    # 生成自定义的整数索引列
    df = client.bars(symbol=code, frequency='day', offset=300)  # 获取最近300日东方财富k线
    custom_index = pd.RangeIndex(start=1, stop=len(df)+1, step=1)
    # 使用自定义的整数索引列作为索引
    df.set_index(custom_index, inplace=True)
    try:
        close = df['close']
    except:
        # 如果是退市股票，直接返回0
        return (0,0,0)
    BBI = tdx_indicator.BBI(close)
    if(datestr==""):
        return BBI[-1]
    else:
        try:
            index = df[df['datetime'].str.contains(datestr)].index-1
            # print(index)
            # print(J[index])
            return BBI[index][0]
        except:
            print("datestr格式不合规 或 该日期没有交易日 或 指定交易日错误")

# print(get_day_kdj("000400", "2024-12-18"))


# get_week_kdj("000400")
# get_day_kdj("000400","2025-01-08")
# print(get_month_kdj("000400","2024-01-05")[-1])
# client = init_create_client()
# print(get_day_kdj("920108",client=client)[0])
# print(get_day_kdj("600900","2025-08-21",client))
# print(get_day_bbi("600900","2025-08-21",client))
# print(get_day_macd("002544","2025-08-22",client))
# df = client.bars(market="881256", frequency='day', offset=300)  # 获取最近300日东方财富k线
# print(df.columns)
# df.to_excel("920108.xlsx")
# df = client.bars(market="BK",symbol="0475", frequency='day', offset=300)  # 获取最近300日东方财富k线
# df = client.bars(symbol="000001", frequency='day', offset=300)  # 获取最近300日东方财富k线
# df = client.k(symbol='881268', frequency=9, offset=30)  # 假设银行板块指数代码是 BK0479
# print(df)

# df = client.bars(symbol='605339', frequency='day', offset=300)  # 获取最近300日东方财富k线
# print(df)


# print(get_day_kdj("0475",client=client))

# print(get_day_kdj("000400",client=client))
# print(get_day_kdj("000400",client=client))
# a = get_cur_data('000400',client).get('year')
# print(a)