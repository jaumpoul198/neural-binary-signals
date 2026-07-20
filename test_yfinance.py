import yfinance as yf

try:
    data = yf.download('EURUSD=X', period='1d', interval='1m')
    print(f"Baixados: {len(data)}")
except Exception as e:
    print(f"Erro: {e}")