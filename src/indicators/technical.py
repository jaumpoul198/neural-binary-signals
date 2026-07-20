"""
Indicadores Técnicos
Coleção completa de indicadores otimizados para timeframes curtos (M1/M5).
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


class TechnicalIndicators:
    """
    Calculadora de indicadores técnicos.

    Todos os indicadores são calculados de forma vetorizada para performance.
    """

    def calculate_all(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """
        Calcula todos os indicadores configurados e retorna valores atuais.

        Args:
            df: DataFrame com OHLCV
            config: Configuração dos indicadores

        Returns:
            Dict com valores atuais de cada indicador
        """
        results = {}

        if config["rsi"]["enabled"]:
            results.update(self._rsi(df, config["rsi"]))

        if config["macd"]["enabled"]:
            results.update(self._macd(df, config["macd"]))

        if config["bollinger_bands"]["enabled"]:
            results.update(self._bollinger(df, config["bollinger_bands"]))

        if config["vwap"]["enabled"]:
            results.update(self._vwap(df))

        if config["stochastic"]["enabled"]:
            results.update(self._stochastic(df, config["stochastic"]))

        if config["atr"]["enabled"]:
            results.update(self._atr(df, config["atr"]))

        if config["ema"]["enabled"]:
            results.update(self._ema(df, config["ema"]))

        if config["adx"]["enabled"]:
            results.update(self._adx(df, config["adx"]))

        if config["cci"]["enabled"]:
            results.update(self._cci(df, config["cci"]))

        if config["williams_r"]["enabled"]:
            results.update(self._williams_r(df, config["williams_r"]))

        if config["momentum"]["enabled"]:
            results.update(self._momentum(df, config["momentum"]))

        if config["obv"]["enabled"]:
            results.update(self._obv(df))

        if config["ichimoku"]["enabled"]:
            results.update(self._ichimoku(df, config["ichimoku"]))

        if config["volume_profile"]["enabled"]:
            results.update(self._volume_profile(df, config["volume_profile"]))

        if config["fibonacci_retracement"]["enabled"]:
            results.update(self._fibonacci(df, config["fibonacci_retracement"]))

        return results

    def _rsi(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Relative Strength Index."""
        period = config["period"]
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return {
            "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0,
            "rsi_prev": float(rsi.iloc[-2]) if len(rsi) > 1 and not pd.isna(rsi.iloc[-2]) else 50.0,
        }

    def _macd(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """MACD (Moving Average Convergence Divergence)."""
        fast = config["fast"]
        slow = config["slow"]
        signal_period = config["signal"]

        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            "macd_signal": float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            "macd_histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0,
            "macd_histogram_prev": float(histogram.iloc[-2]) if len(histogram) > 1 and not pd.isna(histogram.iloc[-2]) else 0.0,
        }

    def _bollinger(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Bollinger Bands."""
        period = config["period"]
        std_dev = config["std_dev"]

        sma = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        current = df["close"].iloc[-1]

        # Posição relativa dentro das bandas (0 = inferior, 1 = superior)
        band_width = upper.iloc[-1] - lower.iloc[-1]
        position = (current - lower.iloc[-1]) / band_width if band_width > 0 else 0.5

        return {
            "bb_upper": float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else current,
            "bb_middle": float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else current,
            "bb_lower": float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else current,
            "bb_width": float(band_width) if not pd.isna(band_width) else 0.0,
            "bb_position": float(np.clip(position, 0, 1)),
            "bb_squeeze": float(std.iloc[-1] / sma.iloc[-1]) if not pd.isna(std.iloc[-1]) else 0.0,
        }

    def _vwap(self, df: pd.DataFrame) -> Dict[str, float]:
        """Volume Weighted Average Price."""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()

        current = df["close"].iloc[-1]
        vwap_current = vwap.iloc[-1]

        # Posição relativa ao VWAP
        daily_range = df["high"].max() - df["low"].min()
        position = (current - vwap_current) / daily_range if daily_range > 0 else 0

        return {
            "vwap": float(vwap_current) if not pd.isna(vwap_current) else current,
            "vwap_position": float(np.clip(position, -1, 1)),
            "vwap_distance": float(abs(current - vwap_current) / current * 100) if current > 0 else 0.0,
        }

    def _stochastic(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Stochastic Oscillator."""
        k_period = config["k_period"]
        d_period = config["d_period"]
        smooth = config["smooth"]

        lowest_low = df["low"].rolling(window=k_period).min()
        highest_high = df["high"].rolling(window=k_period).max()

        k = 100 * ((df["close"] - lowest_low) / (highest_high - lowest_low))
        k = k.rolling(window=smooth).mean()
        d = k.rolling(window=d_period).mean()

        return {
            "stochastic_k": float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50.0,
            "stochastic_d": float(d.iloc[-1]) if not pd.isna(d.iloc[-1]) else 50.0,
            "stochastic_cross": float(k.iloc[-1] - d.iloc[-1]) if not pd.isna(k.iloc[-1]) and not pd.isna(d.iloc[-1]) else 0.0,
        }

    def _atr(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Average True Range."""
        period = config["period"]

        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(window=period).mean()

        current = df["close"].iloc[-1]
        atr_pct = (atr.iloc[-1] / current * 100) if current > 0 else 0

        return {
            "atr": float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0,
            "atr_percent": float(atr_pct) if not pd.isna(atr_pct) else 0.0,
            "atr_ratio": float(atr.iloc[-1] / atr.iloc[-period]) if len(atr) > period and atr.iloc[-period] > 0 else 1.0,
        }

    def _ema(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Exponential Moving Averages."""
        results = {}
        current = df["close"].iloc[-1]

        for period in config["periods"]:
            ema = df["close"].ewm(span=period, adjust=False).mean()
            ema_val = ema.iloc[-1]
            results[f"ema_{period}"] = float(ema_val) if not pd.isna(ema_val) else current
            results[f"ema_{period}_slope"] = float(ema.iloc[-1] - ema.iloc[-5]) if len(ema) > 5 else 0.0

        # EMA Ribbon
        if len(config["periods"]) >= 2:
            ema_fast = results[f"ema_{config['periods'][0]}"]
            ema_slow = results[f"ema_{config['periods'][1]}"]
            results["ema_cross"] = ema_fast - ema_slow

        return results

    def _adx(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Average Directional Index."""
        period = config["period"]

        plus_dm = df["high"].diff()
        minus_dm = df["low"].diff().abs()

        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift()).abs(),
            (df["low"] - df["close"].shift()).abs()
        ], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return {
            "adx": float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0.0,
            "adx_plus_di": float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else 0.0,
            "adx_minus_di": float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 0.0,
            "adx_trend_strength": "strong" if adx.iloc[-1] > config["strong_trend"] else "weak" if not pd.isna(adx.iloc[-1]) else "unknown",
        }

    def _cci(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Commodity Channel Index."""
        period = config["period"]

        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma_tp = tp.rolling(window=period).mean()
        mean_dev = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        cci = (tp - sma_tp) / (0.015 * mean_dev)

        return {
            "cci": float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else 0.0,
            "cci_prev": float(cci.iloc[-2]) if len(cci) > 1 and not pd.isna(cci.iloc[-2]) else 0.0,
        }

    def _williams_r(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Williams %R."""
        period = config["period"]

        highest_high = df["high"].rolling(window=period).max()
        lowest_low = df["low"].rolling(window=period).min()

        wr = -100 * (highest_high - df["close"]) / (highest_high - lowest_low)

        return {
            "williams_r": float(wr.iloc[-1]) if not pd.isna(wr.iloc[-1]) else -50.0,
            "williams_r_prev": float(wr.iloc[-2]) if len(wr) > 1 and not pd.isna(wr.iloc[-2]) else -50.0,
        }

    def _momentum(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Momentum Indicator."""
        period = config["period"]

        momentum = df["close"] - df["close"].shift(period)

        return {
            "momentum": float(momentum.iloc[-1]) if not pd.isna(momentum.iloc[-1]) else 0.0,
            "momentum_normalized": float(momentum.iloc[-1] / df["close"].iloc[-1] * 100) if not pd.isna(momentum.iloc[-1]) and df["close"].iloc[-1] > 0 else 0.0,
        }

    def _obv(self, df: pd.DataFrame) -> Dict[str, float]:
        """On-Balance Volume."""
        obv = (np.sign(df["close"].diff()) * df["volume"]).cumsum()
        obv_ema = obv.ewm(span=20).mean()

        return {
            "obv": float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else 0.0,
            "obv_ema": float(obv_ema.iloc[-1]) if not pd.isna(obv_ema.iloc[-1]) else 0.0,
            "obv_trend": "up" if obv.iloc[-1] > obv_ema.iloc[-1] else "down" if not pd.isna(obv.iloc[-1]) and not pd.isna(obv_ema.iloc[-1]) else "neutral",
        }

    def _ichimoku(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Ichimoku Cloud."""
        tenkan_period = config["tenkan"]
        kijun_period = config["kijun"]
        senkou_period = config["senkou"]

        tenkan_sen = (df["high"].rolling(window=tenkan_period).max() + 
                      df["low"].rolling(window=tenkan_period).min()) / 2
        kijun_sen = (df["high"].rolling(window=kijun_period).max() + 
                     df["low"].rolling(window=kijun_period).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        senkou_span_b = ((df["high"].rolling(window=senkou_period).max() + 
                          df["low"].rolling(window=senkou_period).min()) / 2).shift(kijun_period)

        current = df["close"].iloc[-1]

        cloud_top = max(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1]) if not pd.isna(senkou_span_a.iloc[-1]) and not pd.isna(senkou_span_b.iloc[-1]) else current
        cloud_bottom = min(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1]) if not pd.isna(senkou_span_a.iloc[-1]) and not pd.isna(senkou_span_b.iloc[-1]) else current

        return {
            "ichimoku_tenkan": float(tenkan_sen.iloc[-1]) if not pd.isna(tenkan_sen.iloc[-1]) else current,
            "ichimoku_kijun": float(kijun_sen.iloc[-1]) if not pd.isna(kijun_sen.iloc[-1]) else current,
            "ichimoku_senkou_a": float(senkou_span_a.iloc[-1]) if not pd.isna(senkou_span_a.iloc[-1]) else current,
            "ichimoku_senkou_b": float(senkou_span_b.iloc[-1]) if not pd.isna(senkou_span_b.iloc[-1]) else current,
            "ichimoku_cloud_position": "above" if current > cloud_top else "below" if current < cloud_bottom else "inside",
            "ichimoku_tk_cross": float(tenkan_sen.iloc[-1] - kijun_sen.iloc[-1]) if not pd.isna(tenkan_sen.iloc[-1]) and not pd.isna(kijun_sen.iloc[-1]) else 0.0,
        }

    def _volume_profile(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Volume Profile Analysis."""
        lookback = config["lookback"]

        if len(df) < lookback:
            return {"volume_profile_position": 0.5, "volume_profile_poc": df["close"].iloc[-1]}

        recent = df.tail(lookback)

        # Point of Control (preço com maior volume)
        price_bins = pd.cut(recent["close"], bins=20)
        volume_by_price = recent.groupby(price_bins)["volume"].sum()
        poc_bin = volume_by_price.idxmax()
        poc_price = (poc_bin.left + poc_bin.right) / 2

        # Posição do preço atual no profile
        current = df["close"].iloc[-1]
        price_range = recent["close"].max() - recent["close"].min()
        position = (current - recent["close"].min()) / price_range if price_range > 0 else 0.5

        # Volume delta (compra vs venda estimado)
        buy_volume = recent["volume"] * (recent["close"] > recent["open"])
        sell_volume = recent["volume"] * (recent["close"] < recent["open"])
        volume_delta = buy_volume.sum() - sell_volume.sum()

        return {
            "volume_profile_position": float(np.clip(position, 0, 1)),
            "volume_profile_poc": float(poc_price) if not pd.isna(poc_price) else current,
            "volume_profile_delta": float(volume_delta),
            "volume_profile_delta_ratio": float(volume_delta / recent["volume"].sum()) if recent["volume"].sum() > 0 else 0.0,
        }

    def _fibonacci(self, df: pd.DataFrame, config: Dict) -> Dict[str, float]:
        """Fibonacci Retracement Levels."""
        levels = config["levels"]
        lookback = 50

        if len(df) < lookback:
            return {}

        recent = df.tail(lookback)
        swing_high = recent["high"].max()
        swing_low = recent["low"].min()
        range_size = swing_high - swing_low

        current = df["close"].iloc[-1]

        results = {}
        for level in levels:
            fib_price = swing_high - (range_size * level)
            distance = abs(current - fib_price) / current * 100 if current > 0 else 0
            results[f"fib_{int(level*1000)}"] = float(fib_price)
            results[f"fib_{int(level*1000)}_distance"] = float(distance)

        # Nível Fib mais próximo
        fib_prices = [swing_high - (range_size * level) for level in levels]
        distances = [abs(current - fp) for fp in fib_prices]
        nearest_idx = np.argmin(distances)
        results["fib_nearest_level"] = float(levels[nearest_idx])
        results["fib_nearest_distance"] = float(distances[nearest_idx] / current * 100) if current > 0 else 0.0

        return results
