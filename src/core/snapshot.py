"""
Market Snapshot - Captura fotográfica do mercado
Representa o estado completo do mercado em um momento específico.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class MarketSnapshot:
    """
    Snapshot fotográfico do mercado em um momento específico.

    Captura:
    - Dados de preço (OHLCV)
    - Valores de todos os indicadores
    - Padrões de candlestick detectados
    - Contexto de mercado (tendência, volatilidade)
    """

    timestamp: datetime
    pair: str
    timeframe: str

    # Dados de preço
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float

    # Indicadores
    indicators: Dict[str, float] = field(default_factory=dict)

    # Padrões de candlestick
    candlestick_patterns: List[str] = field(default_factory=list)

    # Contexto
    trend: str = "neutral"  # "up", "down", "neutral"
    volatility_regime: str = "normal"  # "low", "normal", "high"
    session: str = "unknown"  # "asian", "london", "new_york", "overlap"

    # Metadados
    signal_generated: Optional[str] = None  # "CALL", "PUT", None
    signal_confidence: float = 0.0
    result: Optional[str] = None  # "WIN", "LOSS", None (para treinamento)

    def to_feature_vector(self) -> np.ndarray:
        """
        Converte o snapshot em um vetor de features numérico.
        Usado pela memória neural para comparação de similaridade.
        """
        features = []

        # Normalizar preços (variação percentual)
        features.append((self.close_price - self.open_price) / self.open_price)
        features.append((self.high_price - self.low_price) / self.open_price)
        features.append(self.volume / 1000.0)  # Normalizar volume

        # Indicadores normalizados
        indicator_values = []
        for key, value in sorted(self.indicators.items()):
            if isinstance(value, (int, float)) and not np.isnan(value):
                # Normalização por tipo de indicador
                if "rsi" in key.lower() or "stochastic" in key.lower():
                    indicator_values.append(value / 100.0)
                elif "macd" in key.lower():
                    indicator_values.append(np.tanh(value / 100.0))
                elif "adx" in key.lower():
                    indicator_values.append(min(value / 50.0, 1.0))
                elif "atr" in key.lower():
                    indicator_values.append(np.tanh(value / 0.01))
                elif "bb" in key.lower() or "bollinger" in key.lower():
                    indicator_values.append(np.tanh(value))
                else:
                    indicator_values.append(np.tanh(value))
            else:
                indicator_values.append(0.0)

        features.extend(indicator_values)

        # Padrões de candlestick como one-hot
        pattern_features = []
        all_patterns = [
            "hammer", "inverted_hammer", "engulfing_bullish",
            "engulfing_bearish", "morning_star", "evening_star",
            "doji", "shooting_star", "harami", "piercing_line"
        ]
        for pattern in all_patterns:
            pattern_features.append(1.0 if pattern in self.candlestick_patterns else 0.0)
        features.extend(pattern_features)

        # Contexto
        trend_map = {"up": 1.0, "down": -1.0, "neutral": 0.0}
        features.append(trend_map.get(self.trend, 0.0))

        vol_map = {"low": 0.0, "normal": 0.5, "high": 1.0}
        features.append(vol_map.get(self.volatility_regime, 0.5))

        # Preencher ou truncar para tamanho fixo
        target_size = 64
        if len(features) < target_size:
            features.extend([0.0] * (target_size - len(features)))
        else:
            features = features[:target_size]

        return np.array(features, dtype=np.float32)

    def to_dict(self) -> dict:
        """Converte para dicionário serializável."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "pair": self.pair,
            "timeframe": self.timeframe,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "indicators": self.indicators,
            "candlestick_patterns": self.candlestick_patterns,
            "trend": self.trend,
            "volatility_regime": self.volatility_regime,
            "session": self.session,
            "signal_generated": self.signal_generated,
            "signal_confidence": self.signal_confidence,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketSnapshot":
        """Cria snapshot a partir de dicionário."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            pair=data["pair"],
            timeframe=data["timeframe"],
            open_price=data["open"],
            high_price=data["high"],
            low_price=data["low"],
            close_price=data["close"],
            volume=data["volume"],
            indicators=data.get("indicators", {}),
            candlestick_patterns=data.get("candlestick_patterns", []),
            trend=data.get("trend", "neutral"),
            volatility_regime=data.get("volatility_regime", "normal"),
            session=data.get("session", "unknown"),
            signal_generated=data.get("signal_generated"),
            signal_confidence=data.get("signal_confidence", 0.0),
            result=data.get("result"),
        )
