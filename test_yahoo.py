import yfinance as yf
import time

def get_prices():
    assets = {
        'EURUSD': 'EURUSD=X',
        'USDJPY': 'USDJPY=X',
        'GBPUSD': 'GBPUSD=X',
        'AUDUSD': 'AUDUSD=X',
        'BTCUSD': 'BTC-USD',
        'ETHUSD': 'ETH-USD'
    }
    
    prices = {}
    for name, symbol in assets.items():
        try:
            data = yf.download(symbol, period='1d', interval='5m', progress=False)
            if len(data) > 0:
                prices[name] = data['close'].iloc[-1]
        except:
            pass
    
    return prices

while True:
    prices = get_prices()
    print("\n--- PRECOS ---")
    for name, price in prices.items():
        print(f"{name}: {price:.6f}")
    time.sleep(10)