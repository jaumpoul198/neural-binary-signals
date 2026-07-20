"""
Motor de Decisão - Neural Binary Signals
Versão simplificada que funciona com a estrutura atual
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    CALL = "CALL"
    PUT = "PUT"
    NEUTRAL = "NEUTRAL"


class SignalStrength(Enum):
    STRONG = "STRONG"
    MEDIUM = "MEDIUM"
    WEAK = "WEAK"


@dataclass
class Signal:
    symbol: str
    signal_type: SignalType
    confidence: float
    strength: SignalStrength
    timestamp: datetime
    timeframe: str
    reasons: List[str]
    metadata: Dict


class DecisionEngine:
    """
    Motor de Decisão - Análise de indicadores para geração de sinais
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.symbols = self.config.get('pairs', ['EURUSD'])
        
    def analyze(self, data: pd.DataFrame, symbol: str = "UNKNOWN", 
                timeframe: str = "M5", is_otc: bool = False) -> Optional[Signal]:
        """
        Analisa os dados e gera um sinal
        """
        try:
            if len(data) < 50:
                logger.warning(f"Dados insuficientes: {len(data)} candles")
                return None
            
            logger.info(f"Analisando {symbol} - {timeframe}")
            
            # Calcula indicadores básicos
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # Médias móveis
            ema_9 = self._ema(close, 9)
            ema_21 = self._ema(close, 21)
            ema_50 = self._ema(close, 50)
            
            # RSI
            rsi = self._rsi(close, 14)
            
            # Últimos valores
            last_close = close[-1]
            last_ema_9 = ema_9[-1] if len(ema_9) > 0 else last_close
            last_ema_21 = ema_21[-1] if len(ema_21) > 0 else last_close
            last_ema_50 = ema_50[-1] if len(ema_50) > 0 else last_close
            last_rsi = rsi[-1] if len(rsi) > 0 else 50
            
            # Análise de tendência
            trend_score = 0.0
            reasons = []
            
            # EMA Alinhamento
            if last_ema_9 > last_ema_21 > last_ema_50:
                trend_score += 0.4
                reasons.append("✓ EMAs alinhadas (bullish)")
            elif last_ema_9 < last_ema_21 < last_ema_50:
                trend_score -= 0.4
                reasons.append("✓ EMAs alinhadas (bearish)")
            
            # Preço vs EMAs
            if last_close > last_ema_21:
                trend_score += 0.3
                reasons.append("✓ Preço acima da EMA21")
            else:
                trend_score -= 0.3
                reasons.append("✓ Preço abaixo da EMA21")
            
            # RSI
            if last_rsi > 70:
                trend_score -= 0.2
                reasons.append(f"✓ RSI sobrecomprado ({last_rsi:.1f})")
            elif last_rsi < 30:
                trend_score += 0.2
                reasons.append(f"✓ RSI sobrevendido ({last_rsi:.1f})")
            elif 40 < last_rsi < 60:
                reasons.append(f"✓ RSI neutro ({last_rsi:.1f})")
            
            # Confiança
            confidence = (trend_score + 1) / 2
            confidence = np.clip(confidence, 0.3, 0.95)
            
            # Determina sinal
            if trend_score > 0.2:
                signal_type = SignalType.CALL
                reasons.append("📈 Tendência de alta")
            elif trend_score < -0.2:
                signal_type = SignalType.PUT
                reasons.append("📉 Tendência de baixa")
            else:
                signal_type = SignalType.NEUTRAL
                reasons.append("➖ Mercado lateral")
            
            # Força do sinal
            if confidence >= 0.75:
                strength = SignalStrength.STRONG
            elif confidence >= 0.55:
                strength = SignalStrength.MEDIUM
            else:
                strength = SignalStrength.WEAK
            
            reasons.append(f"📊 Score: {confidence:.1%}")
            
            # Metadados
            metadata = {
                'rsi': last_rsi,
                'ema_9': last_ema_9,
                'ema_21': last_ema_21,
                'ema_50': last_ema_50,
                'trend_score': trend_score,
                'timeframe': timeframe,
                'is_otc': is_otc
            }
            
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                strength=strength,
                timestamp=datetime.now(),
                timeframe=timeframe,
                reasons=reasons,
                metadata=metadata
            )
            
            logger.info(f"Sinal: {signal_type} | Confiança: {confidence:.1%}")
            return signal
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return None
    
    def _ema(self, prices, period):
        """Calcula EMA"""
        if len(prices) < period:
            return np.array([prices[-1]] * len(prices))
        
        ema = np.zeros_like(prices)
        ema[:period] = np.mean(prices[:period])
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def _rsi(self, prices, period=14):
        """Calcula RSI"""
        if len(prices) < period + 1:
            return np.array([50] * len(prices))
        
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[period] = 100 - (100 / (1 + rs))
        
        for i in range(period + 1, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi