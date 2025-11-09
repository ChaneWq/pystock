# fetcher.py
from day_index import get_cur_price, init_create_client

def get_current_price(stock_code: str, client) -> float:
    try:
        price = get_cur_price(stock_code, client)
        return float(price)
    except Exception as e:
        print(f"[Fetcher] Error getting price for {stock_code}: {e}")
        return None

def init_client():
    return init_create_client()
