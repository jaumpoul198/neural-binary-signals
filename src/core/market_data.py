"""
Motor de Dados de Mercado
Responsável por buscar, processar e fornecer dados OHLCV.
Suporta Yahoo Finance e dados simulados para OTC.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import websocket
import json
import threading
import time


class MarketDataEngine:
    """
    Motor de dados de mercado com suporte a múltiplas fontes.

    Para OTC: Usa dados simulados baseados em random walk com características
    de volatilidade realistas, já que OTC não tem feed público.

    Para Mercado Aberto: Usa Yahoo Finance e WebSocket quando disponível.
    """

    OTC_PAIRS = {
        "EURUSD-OTC": {"base_volatility": 0.0008, "trend_bias": 0.0},
        "GBPUSD-OTC": {"base_volatility": 0.0010, "trend_bias": 0.0},
        "USDJPY-OTC": {"base_volatility": 0.0009, "trend_bias": 0.0},
        "AUDUSD-OTC": {"base_volatility": 0.0012, "trend_bias": 0.0},
        "USDCAD-OTC": {"base_volatility": 0.0009, "trend_bias": 0.0},
        "EURGBP-OTC": {"base_volatility": 0.0007, "trend_bias": 0.0},
        "EURJPY-OTC": {"base_volatility": 0.0011, "trend_bias": 0.0},
        "GBPJPY-OTC": {"base_volatility": 0.0013, "trend_bias": 0.0},
    }

    OPEN_PAIRS_MAP = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X",
        "EURGBP": "EURGBP=X",
        "EURJPY": "EURJPY=X",
        "GBPJPY": "GBPJPY=X",
        "NZDUSD": "NZDUSD=X",
        "USDCHF": "USDCHF=X",
        "XAUUSD": "GC=F",
        "US30": "^DJI",
    }

    TIMEFRAME_MAP = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "1h",
    }

    def __init__(self):
        self._otc_prices = {pair: self._generate_initial_price(pair) 
                           for pair in self.OTC_PAIRS}
        self._otc_data = {pair: pd.DataFrame() for pair in self.OTC_PAIRS}
        self._running = False
        self._update_thread = None
        self._callbacks = []

    def _generate_initial_price(self, pair: str) -> float:
        """Gera preço inicial realista para par OTC."""
        base_prices = {
            "EURUSD": 1.0850, "GBPUSD": 1.2650, "USDJPY": 149.50,
            "AUDUSD": 0.6550, "USDCAD": 1.3550, "EURGBP": 0.8570,
            "EURJPY": 162.30, "GBPJPY": 189.20,
        }
        clean_pair = pair.replace("-OTC", "")
        return base_prices.get(clean_pair, 1.0000)

    def _simulate_otc_tick(self, pair: str) -> dict:
        """
        Simula um tick OTC com random walk realista.
        Inclui micro-tendências, reversões e clusters de volatilidade.
        """
        config = self.OTC_PAIRS[pair]
        current_price = self._otc_prices[pair]

        # Random walk com drift
        drift = np.random.normal(0, config["base_volatility"] * 0.3)
        shock = np.random.normal(0, config["base_volatility"])

        # Clustering de volatilidade (GARCH-like)
        if np.random.random() < 0.1:
            shock *= 2.5

        new_price = current_price * (1 + drift + shock)
        self._otc_prices[pair] = new_price

        return {
            "timestamp": datetime.now(),
            "price": new_price,
            "pair": pair,
            "spread": config["base_volatility"] * 0.5,
        }

    def get_historical_data(self, pair: str, timeframe: str = "M5", 
                           periods: int = 200) -> pd.DataFrame:
        """
        Obtém dados históricos OHLCV.

        Args:
            pair: Par de moedas (ex: "EURUSD" ou "EURUSD-OTC")
            timeframe: Timeframe (M1, M5, M15)
            periods: Número de candles

        Returns:
            DataFrame com colunas: open, high, low, close, volume
        """
        if pair.endswith("-OTC"):
            return self._get_otc_historical(pair, timeframe, periods)
        else:
            return self._get_open_market_historical(pair, timeframe, periods)

    def _get_otc_historical(self, pair: str, timeframe: str, 
                            periods: int) -> pd.DataFrame:
        """Gera dados históricos OTC simulados com características realistas."""
        config = self.OTC_PAIRS[pair]
        tf_seconds = {"M1": 60, "M5": 300, "M15": 900}.get(timeframe, 300)

        # Gerar candles
        candles = []
        price = self._generate_initial_price(pair)
        now = datetime.now()

        for i in range(periods, 0, -1):
            timestamp = now - timedelta(seconds=i * tf_seconds)

            # Gerar 60 ticks por candle (M5) proporcionalmente
            ticks_per_candle = max(tf_seconds // 5, 1)

            open_price = price
            high_price = price
            low_price = price
            volume = 0

            for _ in range(ticks_per_candle):
                drift = np.random.normal(0, config["base_volatility"] * 0.3)
                shock = np.random.normal(0, config["base_volatility"])
                if np.random.random() < 0.05:
                    shock *= 3
                price *= (1 + drift + shock)
                high_price = max(high_price, price)
                low_price = min(low_price, price)
                volume += abs(np.random.normal(100, 30))

            candles.append({
                "timestamp": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": price,
                "volume": int(volume),
            })

        df = pd.DataFrame(candles)
        df.set_index("timestamp", inplace=True)
        return df

    def _get_open_market_historical(self, pair: str, timeframe: str,
                                    periods: int) -> pd.DataFrame:
        """Obtém dados históricos do mercado aberto via Yahoo Finance."""
        yf_symbol = self.OPEN_PAIRS_MAP.get(pair, pair)
        yf_tf = self.TIMEFRAME_MAP.get(timeframe, "5m")

        # Calcular período necessário
        tf_minutes = {"1m": 1, "5m": 5, "15m": 15}.get(yf_tf, 5)
        total_minutes = periods * tf_minutes
        days_needed = max(total_minutes // (6.5 * 60), 7)

        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=f"{days_needed}d", interval=yf_tf)

            if df.empty:
                # Fallback para dados simulados
                return self._get_otc_historical(f"{pair}-OTC", timeframe, periods)

            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            df.index.name = "timestamp"
            return df.tail(periods)

        except Exception as e:
            print(f"Erro ao buscar dados Yahoo para {pair}: {e}")
            return self._get_otc_historical(f"{pair}-OTC", timeframe, periods)

    def start_live_feed(self, pairs: List[str], callback=None):
        """Inicia feed de dados em tempo real."""
        self._running = True
        if callback:
            self._callbacks.append(callback)

        self._update_thread = threading.Thread(
            target=self._live_feed_loop, args=(pairs,)
        )
        self._update_thread.daemon = True
        self._update_thread.start()

    def _live_feed_loop(self, pairs: List[str]):
        """Loop de atualização em tempo real."""
        while self._running:
            for pair in pairs:
                if pair.endswith("-OTC"):
                    tick = self._simulate_otc_tick(pair)
                    for cb in self._callbacks:
                        cb(tick)
            time.sleep(1)

    def stop_live_feed(self):
        """Para o feed em tempo real."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=2)

    def get_current_price(self, pair: str) -> float:
        """Retorna preço atual do par."""
        if pair.endswith("-OTC"):
            return self._otc_prices.get(pair, 1.0)
        else:
            try:
                yf_symbol = self.OPEN_PAIRS_MAP.get(pair, pair)
                ticker = yf.Ticker(yf_symbol)
                data = ticker.history(period="1d", interval="1m")
                return float(data["Close"].iloc[-1]) if not data.empty else 1.0
            except:
                return 1.0
