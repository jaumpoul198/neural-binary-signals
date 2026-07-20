"""
Provedor de dados OTC (Over-The-Counter)
Simula dados de OTC quando não há volume real
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Optional, Dict

class OTCProvider:
    """
    Provedor de dados para mercado OTC
    Quando não há volume real, usa comportamento estatístico
    """
    
    def __init__(self):
        self.symbols = {
            'EURUSD': {'spread': 0.0002, 'min_move': 0.0001},
            'GBPUSD': {'spread': 0.0003, 'min_move': 0.0001},
            'USDJPY': {'spread': 0.02, 'min_move': 0.01},
            'AUDUSD': {'spread': 0.0003, 'min_move': 0.0001},
            'BTC': {'spread': 50, 'min_move': 10},
            'ETH': {'spread': 10, 'min_move': 2},
        }
    
    def get_historical(self, symbol: str, period: str = '5d', interval: str = '5m') -> pd.DataFrame:
        """
        Gera dados históricos simulados para OTC
        """
        try:
            # Tenta Yahoo primeiro (se disponível)
            import yfinance as yf
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if len(data) > 50:
                print(f"✅ Yahoo: {len(data)} candles para {symbol}")
                return data
            
        except Exception as e:
            print(f"⚠ Yahoo indisponível para {symbol}: {e}")
        
        # Fallback: dados simulados OTC
        print(f"🔄 Gerando dados OTC simulados para {symbol}")
        return self._generate_synthetic_data(symbol)
    
    def _generate_synthetic_data(self, symbol: str, n: int = 100) -> pd.DataFrame:
        """
        Gera dados sintéticos com características OTC
        """
        np.random.seed(random.randint(1, 999999))
        
        # Configuração por símbolo
        config = self.symbols.get(symbol, {'spread': 0.0001, 'min_move': 0.0001})
        spread = config['spread']
        min_move = config['min_move']
        
        # Preço base
        base_price = 1.0850 if 'USD' in symbol else 100
        if symbol == 'BTC':
            base_price = 45000
        elif symbol == 'ETH':
            base_price = 2500
        
        # Gera caminho aleatório (tendência + ruído)
        trend = np.random.choice([-0.0005, 0, 0.0005])
        prices = base_price + np.cumsum(np.random.randn(n) * min_move * 2 + trend)
        prices = np.maximum(prices, base_price * 0.8)
        
        # Cria DataFrame
        dates = pd.date_range(
            start=datetime.now() - timedelta(minutes=n * 5),
            periods=n,
            freq='5min'
        )
        
        df = pd.DataFrame({
            'open': prices[:-1],
            'high': prices[:-1] + np.abs(np.random.randn(n-1) * min_move * 3) + spread,
            'low': prices[:-1] - np.abs(np.random.randn(n-1) * min_move * 3) - spread,
            'close': prices[1:],
            'volume': np.random.randint(100, 5000, n-1)
        }, index=dates[:-1])
        
        # Correção para garantir high >= low
        df['high'] = df[['high', 'low']].max(axis=1)
        df['low'] = df[['low', 'open', 'close']].min(axis=1)
        
        return df
    
    def get_price(self, symbol: str) -> float:
        """
        Obtém preço atual (simulado)
        """
        data = self._generate_synthetic_data(symbol, n=10)
        return round(data['close'].iloc[-1], 4)


# Função auxiliar
def get_otc_data(symbol: str, period: str = '5d', interval: str = '5m') -> pd.DataFrame:
    """
    Função principal para obter dados OTC
    """
    provider = OTCProvider()
    return provider.get_historical(symbol, period, interval)