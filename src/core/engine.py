"""
Signal Engine - Motor de Geração de Sinais
Orquestra indicadores, memória neural e scoring para gerar sinais de alta qualidade.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import json

from .market_data import MarketDataEngine
from .snapshot import MarketSnapshot
from ..indicators.technical import TechnicalIndicators
from ..indicators.candlestick import CandlestickPatterns
from ..memory.neural_memory import NeuralMemory
from ..utils.config_loader import ConfigLoader


class SignalEngine:
    """
    Motor principal de geração de sinais.

    Fluxo:
    1. Recebe dados de mercado
    2. Calcula todos os indicadores
    3. Detecta padrões de candlestick
    4. Consulta memória neural por padrões similares
    5. Calcula score de confiança
    6. Emite sinal se confiança >= threshold
    """

    def __init__(self, config_path: str = "config/settings.json"):
        self.config = ConfigLoader.load(config_path)
        self.market_data = MarketDataEngine()
        self.indicators = TechnicalIndicators()
        self.patterns = CandlestickPatterns()
        self.memory = NeuralMemory(
            similarity_threshold=self.config["memory"]["similarity_threshold"],
            max_patterns=self.config["memory"]["max_patterns"]
        )
        self._signal_history = []
        self._daily_signal_count = 0
        self._last_signal_time = None

    def analyze_pair(self, pair: str, timeframe: str = "M5", 
                     lookback: int = 200) -> Optional[Dict]:
        """
        Analisa um par e retorna sinal se houver oportunidade.

        Returns:
            Dict com sinal ou None se não houver oportunidade
        """
        # Verificar limites diários
        if not self._check_limits():
            return None

        # Obter dados
        df = self.market_data.get_historical_data(pair, timeframe, lookback)
        if df.empty or len(df) < 50:
            return None

        # Criar snapshot
        snapshot = self._create_snapshot(df, pair, timeframe)

        # Calcular score de sinal
        signal_data = self._calculate_signal(snapshot, df)

        if signal_data and signal_data["confidence"] >= self.config["signal_engine"]["min_confidence"]:
            # Registrar sinal
            self._daily_signal_count += 1
            self._last_signal_time = datetime.now()
            self._signal_history.append(signal_data)

            # Atualizar snapshot com sinal
            snapshot.signal_generated = signal_data["direction"]
            snapshot.signal_confidence = signal_data["confidence"]

            # Armazenar na memória (será atualizado com resultado depois)
            self.memory.store(snapshot)

            return signal_data

        return None

    def _create_snapshot(self, df: pd.DataFrame, pair: str, 
                         timeframe: str) -> MarketSnapshot:
        """Cria snapshot fotográfico do mercado atual."""
        latest = df.iloc[-1]

        # Calcular todos os indicadores
        indicator_values = self.indicators.calculate_all(df, self.config["indicators"])

        # Detectar padrões de candlestick
        detected_patterns = self.patterns.detect_all(df)

        # Determinar tendência
        trend = self._determine_trend(df)

        # Determinar regime de volatilidade
        volatility = self._determine_volatility(df)

        # Determinar sessão
        session = self._determine_session()

        return MarketSnapshot(
            timestamp=datetime.now(),
            pair=pair,
            timeframe=timeframe,
            open_price=float(latest["open"]),
            high_price=float(latest["high"]),
            low_price=float(latest["low"]),
            close_price=float(latest["close"]),
            volume=float(latest["volume"]),
            indicators=indicator_values,
            candlestick_patterns=detected_patterns,
            trend=trend,
            volatility_regime=volatility,
            session=session,
        )

    def _calculate_signal(self, snapshot: MarketSnapshot, 
                          df: pd.DataFrame) -> Optional[Dict]:
        """
        Calcula sinal baseado em confluência de indicadores e memória neural.
        """
        scores = {"CALL": 0.0, "PUT": 0.0}
        confluence_count = {"CALL": 0, "PUT": 0}
        reasons = []

        # 1. RSI
        rsi = snapshot.indicators.get("rsi", 50)
        if rsi < self.config["indicators"]["rsi"]["oversold"]:
            scores["CALL"] += 15 * self.config["indicators"]["rsi"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > self.config["indicators"]["rsi"]["overbought"]:
            scores["PUT"] += 15 * self.config["indicators"]["rsi"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append(f"RSI overbought ({rsi:.1f})")

        # 2. MACD
        macd = snapshot.indicators.get("macd_histogram", 0)
        macd_signal = snapshot.indicators.get("macd_signal", 0)
        if macd > 0 and macd > macd_signal:
            scores["CALL"] += 12 * self.config["indicators"]["macd"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append("MACD histograma positivo")
        elif macd < 0 and macd < macd_signal:
            scores["PUT"] += 12 * self.config["indicators"]["macd"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append("MACD histograma negativo")

        # 3. Bollinger Bands
        bb_position = snapshot.indicators.get("bb_position", 0.5)
        if bb_position < 0.1:
            scores["CALL"] += 10 * self.config["indicators"]["bollinger_bands"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append("Preço na banda inferior BB")
        elif bb_position > 0.9:
            scores["PUT"] += 10 * self.config["indicators"]["bollinger_bands"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append("Preço na banda superior BB")

        # 4. Stochastic
        stoch_k = snapshot.indicators.get("stochastic_k", 50)
        stoch_d = snapshot.indicators.get("stochastic_d", 50)
        if stoch_k < self.config["indicators"]["stochastic"]["oversold"] and stoch_k > stoch_d:
            scores["CALL"] += 10 * self.config["indicators"]["stochastic"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append(f"Stochastic oversold cruzando para cima ({stoch_k:.1f})")
        elif stoch_k > self.config["indicators"]["stochastic"]["overbought"] and stoch_k < stoch_d:
            scores["PUT"] += 10 * self.config["indicators"]["stochastic"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append(f"Stochastic overbought cruzando para baixo ({stoch_k:.1f})")

        # 5. EMA Cross
        ema9 = snapshot.indicators.get("ema_9", 0)
        ema21 = snapshot.indicators.get("ema_21", 0)
        if ema9 > ema21:
            scores["CALL"] += 8 * self.config["indicators"]["ema"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append("EMA9 > EMA21 (tendência de alta)")
        elif ema9 < ema21:
            scores["PUT"] += 8 * self.config["indicators"]["ema"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append("EMA9 < EMA21 (tendência de baixa)")

        # 6. ADX - força da tendência
        adx = snapshot.indicators.get("adx", 0)
        if adx > self.config["indicators"]["adx"]["strong_trend"]:
            # Em tendência forte, seguir a tendência
            if snapshot.trend == "up":
                scores["CALL"] += 10 * self.config["indicators"]["adx"]["weight"]
                confluence_count["CALL"] += 1
                reasons.append(f"ADX forte ({adx:.1f}) + tendência de alta")
            elif snapshot.trend == "down":
                scores["PUT"] += 10 * self.config["indicators"]["adx"]["weight"]
                confluence_count["PUT"] += 1
                reasons.append(f"ADX forte ({adx:.1f}) + tendência de baixa")

        # 7. Padrões de Candlestick
        for pattern in snapshot.candlestick_patterns:
            bullish_patterns = ["hammer", "inverted_hammer", "engulfing_bullish", 
                               "morning_star", "piercing_line"]
            bearish_patterns = ["engulfing_bearish", "evening_star", "shooting_star"]

            if pattern in bullish_patterns:
                scores["CALL"] += 18 * self.config["signal_engine"]["candlestick_patterns"]["weight"]
                confluence_count["CALL"] += 1
                reasons.append(f"Padrão {pattern} (bullish)")
            elif pattern in bearish_patterns:
                scores["PUT"] += 18 * self.config["signal_engine"]["candlestick_patterns"]["weight"]
                confluence_count["PUT"] += 1
                reasons.append(f"Padrão {pattern} (bearish)")

        # 8. Memória Neural - Consultar padrões similares
        if self.config["memory"]["enabled"] and len(self.memory.patterns) >= self.config["memory"]["min_history_for_prediction"]:
            similar = self.memory.find_similar(snapshot, top_k=5)
            if similar:
                neural_call_score = 0
                neural_put_score = 0
                neural_count = 0

                for pattern, similarity in similar:
                    if pattern.result == "WIN":
                        if pattern.signal_generated == "CALL":
                            neural_call_score += similarity
                        elif pattern.signal_generated == "PUT":
                            neural_put_score += similarity
                        neural_count += 1

                if neural_count > 0:
                    neural_boost = 20
                    if neural_call_score > neural_put_score:
                        scores["CALL"] += neural_boost * (neural_call_score / neural_count)
                        reasons.append(f"Memória neural: {neural_count} padrões CALL vencedores similares")
                    else:
                        scores["PUT"] += neural_boost * (neural_put_score / neural_count)
                        reasons.append(f"Memória neural: {neural_count} padrões PUT vencedores similares")

        # 9. VWAP
        vwap_position = snapshot.indicators.get("vwap_position", 0)
        if vwap_position < -0.5:
            scores["CALL"] += 8 * self.config["indicators"]["vwap"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append("Preço abaixo do VWAP (potencial reversão)")
        elif vwap_position > 0.5:
            scores["PUT"] += 8 * self.config["indicators"]["vwap"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append("Preço acima do VWAP (potencial reversão)")

        # 10. Volume Profile
        vp_position = snapshot.indicators.get("volume_profile_position", 0.5)
        if vp_position < 0.2:
            scores["CALL"] += 6 * self.config["indicators"]["volume_profile"]["weight"]
            confluence_count["CALL"] += 1
            reasons.append("Volume acumulado na base (suporte)")
        elif vp_position > 0.8:
            scores["PUT"] += 6 * self.config["indicators"]["volume_profile"]["weight"]
            confluence_count["PUT"] += 1
            reasons.append("Volume acumulado no topo (resistência)")

        # Determinar direção vencedora
        direction = "CALL" if scores["CALL"] > scores["PUT"] else "PUT"
        confidence = max(scores["CALL"], scores["PUT"])

        # Normalizar confiança para 0-100
        confidence = min(confidence, 100)

        # Verificar confluência mínima
        if confluence_count[direction] < self.config["signal_engine"]["confluence_required"]:
            return None

        # Verificar se há divergência forte no outro lado
        opposite = "PUT" if direction == "CALL" else "CALL"
        if scores[opposite] > scores[direction] * 0.7:
            return None  # Muita divergência, sinal fraco

        return {
            "timestamp": datetime.now().isoformat(),
            "pair": snapshot.pair,
            "timeframe": snapshot.timeframe,
            "direction": direction,
            "confidence": round(confidence, 1),
            "confluence": confluence_count[direction],
            "score_call": round(scores["CALL"], 1),
            "score_put": round(scores["PUT"], 1),
            "reasons": reasons,
            "price": snapshot.close_price,
            "snapshot": snapshot.to_dict(),
        }

    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determina tendência baseada em EMAs."""
        if len(df) < 50:
            return "neutral"

        ema20 = df["close"].ewm(span=20).mean().iloc[-1]
        ema50 = df["close"].ewm(span=50).mean().iloc[-1]
        current = df["close"].iloc[-1]

        if current > ema20 > ema50:
            return "up"
        elif current < ema20 < ema50:
            return "down"
        return "neutral"

    def _determine_volatility(self, df: pd.DataFrame) -> str:
        """Determina regime de volatilidade."""
        if len(df) < 20:
            return "normal"

        atr = self._calculate_atr(df, 14)
        avg_atr = df["close"].rolling(50).apply(
            lambda x: self._calculate_atr(x.to_frame().assign(
                high=x, low=x, open=x, close=x
            ).reset_index(drop=True), 14)
        ).mean()

        if pd.isna(atr) or pd.isna(avg_atr):
            return "normal"

        ratio = atr / avg_atr if avg_atr > 0 else 1

        if ratio > 1.5:
            return "high"
        elif ratio < 0.7:
            return "low"
        return "normal"

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula ATR."""
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean().iloc[-1]

    def _determine_session(self) -> str:
        """Determina sessão de mercado baseada no horário UTC."""
        from datetime import datetime, timezone
        hour = datetime.now(timezone.utc).hour

        if 0 <= hour < 8:
            return "asian"
        elif 8 <= hour < 13:
            return "london"
        elif 13 <= hour < 17:
            return "overlap"  # Londres + Nova York
        elif 17 <= hour < 22:
            return "new_york"
        else:
            return "asian"

    def _check_limits(self) -> bool:
        """Verifica se ainda pode gerar sinais hoje."""
        max_signals = self.config["risk_management"]["max_daily_signals"]
        if self._daily_signal_count >= max_signals:
            return False

        cooldown = self.config["risk_management"]["cooldown_between_signals_seconds"]
        if self._last_signal_time:
            from datetime import datetime
            elapsed = (datetime.now() - self._last_signal_time).total_seconds()
            if elapsed < cooldown:
                return False

        return True

    def update_signal_result(self, signal_id: str, result: str):
        """
        Atualiza o resultado de um sinal na memória neural.
        Deve ser chamado após o fechamento da vela.

        Args:
            signal_id: Identificador do sinal
            result: "WIN" ou "LOSS"
        """
        # Encontrar snapshot correspondente e atualizar
        for pattern in self.memory.patterns:
            if hasattr(pattern, '_signal_id') and pattern._signal_id == signal_id:
                pattern.result = result
                break

    def get_stats(self) -> Dict:
        """Retorna estatísticas do engine."""
        return {
            "daily_signals": self._daily_signal_count,
            "total_patterns_memory": len(self.memory.patterns),
            "signal_history_count": len(self._signal_history),
            "last_signal": self._last_signal_time.isoformat() if self._last_signal_time else None,
        }
