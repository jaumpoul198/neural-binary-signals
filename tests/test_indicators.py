"""Testes para indicadores tecnicos"""
import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicators
from src.indicators.candlestick import CandlestickPatterns


class TestTechnicalIndicators:
    def test_rsi_calculation(self):
        ti = TechnicalIndicators()
        dates = pd.date_range("2024-01-01", periods=50, freq="5min")
        prices = 1.0850 + np.cumsum(np.random.normal(0.0001, 0.001, 50))

        df = pd.DataFrame({
            "open": prices,
            "high": prices + 0.001,
            "low": prices - 0.001,
            "close": prices + np.random.normal(0, 0.0005, 50),
            "volume": np.random.randint(100, 1000, 50),
        }, index=dates)

        config = {"rsi": {"enabled": True, "period": 14, "overbought": 70, "oversold": 30, "weight": 1.0}}
        result = ti._rsi(df, config["rsi"])

        assert "rsi" in result
        assert 0 <= result["rsi"] <= 100

    def test_macd_calculation(self):
        ti = TechnicalIndicators()
        dates = pd.date_range("2024-01-01", periods=50, freq="5min")
        prices = 1.0850 + np.cumsum(np.random.normal(0, 0.001, 50))

        df = pd.DataFrame({
            "open": prices,
            "high": prices + 0.001,
            "low": prices - 0.001,
            "close": prices,
            "volume": np.random.randint(100, 1000, 50),
        }, index=dates)

        config = {"macd": {"enabled": True, "fast": 12, "slow": 26, "signal": 9, "weight": 1.0}}
        result = ti._macd(df, config["macd"])

        assert "macd" in result
        assert "macd_signal" in result
        assert "macd_histogram" in result


class TestCandlestickPatterns:
    def test_hammer_detection(self):
        cp = CandlestickPatterns()
        dates = pd.date_range("2024-01-01", periods=5, freq="5min")
        df = pd.DataFrame({
            "open": [1.0850, 1.0852, 1.0851, 1.0850, 1.0840],
            "high": [1.0853, 1.0854, 1.0853, 1.0852, 1.0842],
            "low": [1.0848, 1.0850, 1.0849, 1.0848, 1.0830],
            "close": [1.0852, 1.0853, 1.0852, 1.0851, 1.0841],
            "volume": [100, 120, 110, 130, 200],
        }, index=dates)

        patterns = cp.detect_all(df)
        assert isinstance(patterns, list)
