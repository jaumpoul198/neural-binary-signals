"""
Padrões de Candlestick
Detecção automática de padrões de reversão e continuação.
"""

import numpy as np
import pandas as pd
from typing import List


class CandlestickPatterns:
    """
    Detector de padrões de candlestick.

    Detecta padrões clássicos otimizados para timeframes curtos.
    """

    def detect_all(self, df: pd.DataFrame) -> List[str]:
        """
        Detecta todos os padrões de candlestick no último candle.

        Args:
            df: DataFrame com OHLCV (mínimo 5 candles)

        Returns:
            Lista de padrões detectados
        """
        if len(df) < 5:
            return []

        patterns = []

        # Padrões de 1 candle
        if self._is_hammer(df):
            patterns.append("hammer")
        if self._is_inverted_hammer(df):
            patterns.append("inverted_hammer")
        if self._is_doji(df):
            patterns.append("doji")
        if self._is_shooting_star(df):
            patterns.append("shooting_star")

        # Padrões de 2 candles
        if self._is_engulfing_bullish(df):
            patterns.append("engulfing_bullish")
        if self._is_engulfing_bearish(df):
            patterns.append("engulfing_bearish")
        if self._is_harami(df):
            patterns.append("harami")

        # Padrões de 3 candles
        if self._is_morning_star(df):
            patterns.append("morning_star")
        if self._is_evening_star(df):
            patterns.append("evening_star")
        if self._is_piercing_line(df):
            patterns.append("piercing_line")

        return patterns

    def _get_last_candles(self, df: pd.DataFrame, n: int = 1):
        """Retorna os últimos n candles como dicts."""
        candles = []
        for i in range(-n, 0):
            candles.append({
                "open": df["open"].iloc[i],
                "high": df["high"].iloc[i],
                "low": df["low"].iloc[i],
                "close": df["close"].iloc[i],
            })
        return candles

    def _body_size(self, candle: dict) -> float:
        """Tamanho do corpo do candle."""
        return abs(candle["close"] - candle["open"])

    def _upper_shadow(self, candle: dict) -> float:
        """Sombra superior."""
        return candle["high"] - max(candle["open"], candle["close"])

    def _lower_shadow(self, candle: dict) -> float:
        """Sombra inferior."""
        return min(candle["open"], candle["close"]) - candle["low"]

    def _total_range(self, candle: dict) -> float:
        """Range total do candle."""
        return candle["high"] - candle["low"]

    def _is_bullish(self, candle: dict) -> bool:
        """Verifica se o candle é de alta."""
        return candle["close"] > candle["open"]

    def _is_bearish(self, candle: dict) -> bool:
        """Verifica se o candle é de baixa."""
        return candle["close"] < candle["open"]

    def _is_hammer(self, df: pd.DataFrame) -> bool:
        """
        Martelo - padrão de reversão de baixa.
        Corpo pequeno na parte superior, sombra inferior longa (2x+ o corpo).
        """
        c = self._get_last_candles(df, 1)[0]
        body = self._body_size(c)
        total = self._total_range(c)
        lower = self._lower_shadow(c)
        upper = self._upper_shadow(c)

        if total == 0 or body == 0:
            return False

        # Corpo pequeno (< 30% do range)
        small_body = body / total < 0.3
        # Sombra inferior longa (> 2x o corpo)
        long_lower = lower > body * 2
        # Sombra superior mínima (< 10% do range)
        small_upper = upper / total < 0.1
        # Após tendência de baixa (verificar contexto)

        return small_body and long_lower and small_upper and self._is_bullish(c)

    def _is_inverted_hammer(self, df: pd.DataFrame) -> bool:
        """
        Martelo Invertido - padrão de reversão de baixa.
        Corpo pequeno na parte inferior, sombra superior longa.
        """
        c = self._get_last_candles(df, 1)[0]
        body = self._body_size(c)
        total = self._total_range(c)
        lower = self._lower_shadow(c)
        upper = self._upper_shadow(c)

        if total == 0 or body == 0:
            return False

        small_body = body / total < 0.3
        long_upper = upper > body * 2
        small_lower = lower / total < 0.1

        return small_body and long_upper and small_lower and self._is_bullish(c)

    def _is_doji(self, df: pd.DataFrame) -> bool:
        """
        Doji - indecisão do mercado.
        Corpo muito pequeno (< 5% do range total).
        """
        c = self._get_last_candles(df, 1)[0]
        body = self._body_size(c)
        total = self._total_range(c)

        if total == 0:
            return False

        return body / total < 0.05

    def _is_shooting_star(self, df: pd.DataFrame) -> bool:
        """
        Estrela Cadente - padrão de reversão de alta.
        Similar ao martelo invertido mas em contexto de alta.
        """
        c = self._get_last_candles(df, 1)[0]
        body = self._body_size(c)
        total = self._total_range(c)
        lower = self._lower_shadow(c)
        upper = self._upper_shadow(c)

        if total == 0 or body == 0:
            return False

        small_body = body / total < 0.3
        long_upper = upper > body * 2
        small_lower = lower / total < 0.1

        return small_body and long_upper and small_lower and self._is_bearish(c)

    def _is_engulfing_bullish(self, df: pd.DataFrame) -> bool:
        """
        Engolfo de Alta - candle de alta engolfe candle de baixa anterior.
        """
        c1, c2 = self._get_last_candles(df, 2)

        if not self._is_bearish(c1) or not self._is_bullish(c2):
            return False

        # Candle 2 engloba completamente o corpo do candle 1
        body1 = self._body_size(c1)
        body2 = self._body_size(c2)

        return (c2["open"] < c1["close"] and 
                c2["close"] > c1["open"] and 
                body2 > body1 * 1.2)

    def _is_engulfing_bearish(self, df: pd.DataFrame) -> bool:
        """
        Engolfo de Baixa - candle de baixa engolfe candle de alta anterior.
        """
        c1, c2 = self._get_last_candles(df, 2)

        if not self._is_bullish(c1) or not self._is_bearish(c2):
            return False

        body1 = self._body_size(c1)
        body2 = self._body_size(c2)

        return (c2["open"] > c1["close"] and 
                c2["close"] < c1["open"] and 
                body2 > body1 * 1.2)

    def _is_harami(self, df: pd.DataFrame) -> bool:
        """
        Harami - candle pequeno dentro do corpo do candle anterior grande.
        Sinal de possível reversão.
        """
        c1, c2 = self._get_last_candles(df, 2)

        body1 = self._body_size(c1)
        body2 = self._body_size(c2)

        # Candle 1 deve ser grande
        if body1 / self._total_range(c1) < 0.5:
            return False

        # Candle 2 deve estar completamente dentro do corpo do candle 1
        upper1 = max(c1["open"], c1["close"])
        lower1 = min(c1["open"], c1["close"])
        upper2 = max(c2["open"], c2["close"])
        lower2 = min(c2["open"], c2["close"])

        return (body2 < body1 * 0.5 and 
                upper2 < upper1 and 
                lower2 > lower1)

    def _is_morning_star(self, df: pd.DataFrame) -> bool:
        """
        Estrela da Manhã - padrão de 3 candles de reversão de baixa.
        Baixa -> Doji/pequeno -> Alta engolfando.
        """
        if len(df) < 3:
            return False

        c1, c2, c3 = self._get_last_candles(df, 3)

        # Candle 1: Baixa forte
        if not self._is_bearish(c1):
            return False

        body1 = self._body_size(c1)
        if body1 / self._total_range(c1) < 0.6:
            return False

        # Candle 2: Pequeno ou doji (gap down ideal)
        body2 = self._body_size(c2)
        if body2 > body1 * 0.3:
            return False

        # Candle 3: Alta forte que fecha acima do meio do candle 1
        if not self._is_bullish(c3):
            return False

        body3 = self._body_size(c3)
        mid1 = (c1["open"] + c1["close"]) / 2

        return body3 > body1 * 0.5 and c3["close"] > mid1

    def _is_evening_star(self, df: pd.DataFrame) -> bool:
        """
        Estrela da Noite - padrão de 3 candles de reversão de alta.
        Alta -> Doji/pequeno -> Baixa engolfando.
        """
        if len(df) < 3:
            return False

        c1, c2, c3 = self._get_last_candles(df, 3)

        # Candle 1: Alta forte
        if not self._is_bullish(c1):
            return False

        body1 = self._body_size(c1)
        if body1 / self._total_range(c1) < 0.6:
            return False

        # Candle 2: Pequeno ou doji
        body2 = self._body_size(c2)
        if body2 > body1 * 0.3:
            return False

        # Candle 3: Baixa forte que fecha abaixo do meio do candle 1
        if not self._is_bearish(c3):
            return False

        body3 = self._body_size(c3)
        mid1 = (c1["open"] + c1["close"]) / 2

        return body3 > body1 * 0.5 and c3["close"] < mid1

    def _is_piercing_line(self, df: pd.DataFrame) -> bool:
        """
        Linha Perfurante - padrão de 2 candles de reversão de baixa.
        Baixa forte seguida de alta que fecha acima do meio do candle anterior.
        """
        c1, c2 = self._get_last_candles(df, 2)

        if not self._is_bearish(c1) or not self._is_bullish(c2):
            return False

        body1 = self._body_size(c1)
        body2 = self._body_size(c2)

        # Candle 1 deve ser grande
        if body1 / self._total_range(c1) < 0.5:
            return False

        # Candle 2 abre abaixo do fechamento do candle 1 (gap down)
        # e fecha acima do meio do candle 1
        mid1 = (c1["open"] + c1["close"]) / 2

        return (c2["open"] < c1["close"] and 
                c2["close"] > mid1 and 
                body2 > body1 * 0.5)
