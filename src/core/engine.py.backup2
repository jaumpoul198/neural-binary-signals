"""
Motor de Decisão Central - Neural Binary Signals
Versão: 2.0 - Intelligent Decision Engine

Integra todos os indicadores, filtros e análises para gerar sinais
com confidence score explicável.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from ..indicators.technical import TechnicalIndicators
from ..indicators.candlestick import CandlestickPatterns
from ..analysis.trend.trend_detector import TrendDetector
from ..analysis.trend.support_resistance import SupportResistance
from ..analysis.filters.market_filter import MarketFilter
from ..analysis.patterns.candle_patterns import CandlePatternAnalyzer
from ..analysis.scoring.confidence import ConfidenceScorer
from ..analysis.scoring.explainer import SignalExplainer
from ..models.signal import Signal, SignalType, SignalStrength

logger = logging.getLogger(__name__)


class MarketContext(Enum):
    """Contexto de mercado para adaptação da análise"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    OTC = "otc"
    BREAKOUT = "breakout"


@dataclass
class AnalysisFactors:
    """Todos os fatores analisados para um sinal"""
    # Tendência
    trend_direction: float = 0.0
    trend_strength: float = 0.0
    ema_alignment: float = 0.0
    sma_alignment: float = 0.0
    vwap_position: float = 0.0
    
    # Momento
    rsi_value: float = 50.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    momentum: float = 0.0
    adx_value: float = 25.0
    
    # Volatilidade
    atr_value: float = 0.0
    bollinger_position: float = 0.0
    bollinger_width: float = 0.0
    volatility_regime: str = "normal"
    
    # Price Action
    candle_pattern: str = "none"
    pattern_strength: float = 0.0
    support_distance: float = 0.0
    resistance_distance: float = 0.0
    breakout_level: float = 0.0
    pullback_depth: float = 0.0
    
    # Volume (quando disponível)
    volume_trend: float = 0.0
    volume_spike: bool = False
    volume_confirmation: float = 0.0
    
    # Contexto
    market_context: MarketContext = MarketContext.RANGING
    timeframe: str = "M5"
    is_otc: bool = False
    
    # Scores parciais (calculados)
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volatility_score: float = 0.0
    price_action_score: float = 0.0
    volume_score: float = 0.0
    context_score: float = 0.0
    
    # Confiança final
    confidence: float = 0.0
    signal_type: Optional[SignalType] = None
    reasons: List[str] = field(default_factory=list)


class DecisionEngine:
    """
    Motor de Decisão Central - Integra todos os componentes
    
    Pipeline:
    1. Coleta de dados
    2. Cálculo de indicadores
    3. Análise de tendência
    4. Análise de momento
    5. Análise de volatilidade
    6. Price Action
    7. Contexto de mercado
    8. Score de confiança
    9. Geração de sinal com explicação
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Inicializa componentes
        self.technical = TechnicalIndicators()
        self.candlestick = CandlestickPatterns()
        self.trend_detector = TrendDetector()
        self.support_resistance = SupportResistance()
        self.market_filter = MarketFilter()
        self.pattern_analyzer = CandlePatternAnalyzer()
        self.confidence_scorer = ConfidenceScorer()
        self.explainer = SignalExplainer()
        
        # Pesos dos fatores (configuráveis)
        self.weights = {
            'trend': 0.25,
            'momentum': 0.20,
            'price_action': 0.20,
            'volatility': 0.15,
            'volume': 0.10,
            'context': 0.10
        }
        
        # Thresholds
        self.thresholds = {
            'strong_trend': 0.7,
            'weak_trend': 0.3,
            'oversold_rsi': 30,
            'overbought_rsi': 70,
            'high_volatility': 1.5,
            'low_volatility': 0.5,
            'min_confidence': 0.6
        }
        
        logger.info("Decision Engine inicializado")
    
    def analyze(self, data: pd.DataFrame, symbol: str = "UNKNOWN", 
                timeframe: str = "M5", is_otc: bool = False) -> Optional[Signal]:
        """
        Pipeline completo de análise
        
        Args:
            data: DataFrame com OHLCV
            symbol: Símbolo do ativo
            timeframe: Timeframe (M1, M5, M15)
            is_otc: Se é mercado OTC
            
        Returns:
            Signal com análise completa ou None
        """
        try:
            if len(data) < 50:
                logger.warning(f"Dados insuficientes para análise: {len(data)} candles")
                return None
            
            logger.info(f"Analisando {symbol} - {timeframe} - OTC={is_otc}")
            
            # 1. Extrai indicadores
            indicators = self._calculate_indicators(data)
            
            # 2. Análise de tendência
            trend_analysis = self._analyze_trend(data, indicators)
            
            # 3. Análise de momento
            momentum_analysis = self._analyze_momentum(indicators)
            
            # 4. Análise de volatilidade
            volatility_analysis = self._analyze_volatility(data, indicators)
            
            # 5. Price Action
            price_action = self._analyze_price_action(data, indicators)
            
            # 6. Análise de volume (adaptado para OTC)
            volume_analysis = self._analyze_volume(data, is_otc)
            
            # 7. Contexto de mercado
            context = self._determine_context(data, indicators, is_otc)
            
            # 8. Monta todos os fatores
            factors = self._assemble_factors(
                data, indicators, trend_analysis, momentum_analysis,
                volatility_analysis, price_action, volume_analysis, context,
                timeframe, is_otc
            )
            
            # 9. Calcula scores por categoria
            factors = self._calculate_category_scores(factors)
            
            # 10. Score de confiança final
            factors = self._calculate_confidence(factors)
            
            # 11. Gera sinal
            signal = self._generate_signal(symbol, timeframe, factors)
            
            # 12. Explicação
            signal = self._add_explanation(signal, factors)
            
            logger.info(f"Sinal gerado: {signal.signal_type} com confiança {signal.confidence:.2%}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return None
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calcula todos os indicadores técnicos"""
        indicators = {}
        
        try:
            # Médias móveis
            indicators['ema_9'] = self.technical.ema(data, 9)
            indicators['ema_21'] = self.technical.ema(data, 21)
            indicators['ema_50'] = self.technical.ema(data, 50)
            indicators['sma_20'] = self.technical.sma(data, 20)
            indicators['sma_50'] = self.technical.sma(data, 50)
            indicators['sma_200'] = self.technical.sma(data, 200)
            
            # VWAP (volume weighted average price)
            indicators['vwap'] = self.technical.vwap(data)
            
            # Osciladores
            indicators['rsi'] = self.technical.rsi(data, 14)
            indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = \
                self.technical.macd(data)
            indicators['adx'] = self.technical.adx(data, 14)
            
            # Volatilidade
            indicators['atr'] = self.technical.atr(data, 14)
            indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = \
                self.technical.bollinger_bands(data, 20, 2)
            
            # Momento
            indicators['momentum'] = self.technical.momentum(data, 10)
            indicators['roc'] = self.technical.roc(data, 10)
            
            # Volume
            indicators['volume_sma'] = self.technical.sma_volume(data, 20)
            
            # Candles
            indicators['candle_pattern'] = self.candlestick.detect_pattern(data)
            
        except Exception as e:
            logger.error(f"Erro ao calcular indicadores: {e}")
            indicators['error'] = str(e)
        
        return indicators
    
    def _analyze_trend(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """Análise detalhada de tendência"""
        analysis = {
            'direction': 0.0,
            'strength': 0.0,
            'alignment': 0.0
        }
        
        try:
            close = data['close'].values
            last_close = close[-1] if len(close) > 0 else 0
            
            # EMA Alignment (20 fatores: 9, 21, 50)
            ema_values = []
            for ema_key in ['ema_9', 'ema_21', 'ema_50']:
                if ema_key in indicators and not pd.isna(indicators[ema_key][-1]):
                    ema_values.append(indicators[ema_key][-1])
            
            if ema_values:
                # Verifica alinhamento: EMA9 > EMA21 > EMA50 (bullish)
                is_bullish_aligned = all(
                    ema_values[i] > ema_values[i+1] 
                    for i in range(len(ema_values)-1)
                )
                is_bearish_aligned = all(
                    ema_values[i] < ema_values[i+1] 
                    for i in range(len(ema_values)-1)
                )
                
                if is_bullish_aligned:
                    analysis['alignment'] = 1.0
                elif is_bearish_aligned:
                    analysis['alignment'] = -1.0
                else:
                    analysis['alignment'] = 0.0
            
            # VWAP Position
            if 'vwap' in indicators and not pd.isna(indicators['vwap'][-1]):
                vwap = indicators['vwap'][-1]
                if last_close > vwap * 1.005:
                    analysis['vwap_position'] = 1.0
                elif last_close < vwap * 0.995:
                    analysis['vwap_position'] = -1.0
                else:
                    analysis['vwap_position'] = 0.0
            
            # ADX para força da tendência
            if 'adx' in indicators and not pd.isna(indicators['adx'][-1]):
                adx = indicators['adx'][-1]
                if adx > 25:
                    analysis['strength'] = min(1.0, (adx - 20) / 30)
                else:
                    analysis['strength'] = 0.0
            
            # Direção baseada em preço vs EMAs
            if 'ema_21' in indicators and not pd.isna(indicators['ema_21'][-1]):
                ema_21 = indicators['ema_21'][-1]
                if last_close > ema_21:
                    analysis['direction'] += 0.5
                else:
                    analysis['direction'] -= 0.5
            
            if 'ema_50' in indicators and not pd.isna(indicators['ema_50'][-1]):
                ema_50 = indicators['ema_50'][-1]
                if last_close > ema_50:
                    analysis['direction'] += 0.5
                else:
                    analysis['direction'] -= 0.5
            
            # Normaliza direção
            analysis['direction'] = np.clip(analysis['direction'] / 2, -1, 1)
            
        except Exception as e:
            logger.error(f"Erro na análise de tendência: {e}")
        
        return analysis
    
    def _analyze_momentum(self, indicators: Dict) -> Dict:
        """Análise de momento"""
        analysis = {
            'rsi_signal': 0.0,
            'macd_signal': 0.0,
            'momentum': 0.0,
            'overall': 0.0
        }
        
        try:
            # RSI
            if 'rsi' in indicators and not pd.isna(indicators['rsi'][-1]):
                rsi = indicators['rsi'][-1]
                if rsi > 70:
                    analysis['rsi_signal'] = -0.5  # Sobrecomprado (bearish)
                elif rsi < 30:
                    analysis['rsi_signal'] = 0.5   # Sobrevencido (bullish)
                else:
                    analysis['rsi_signal'] = (rsi - 50) / 20
            
            # MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd'][-1]
                signal = indicators['macd_signal'][-1]
                hist = indicators['macd_hist'][-1]
                
                if not pd.isna(macd) and not pd.isna(signal):
                    if macd > signal:
                        analysis['macd_signal'] = 0.5
                        if hist > 0:
                            analysis['macd_signal'] += 0.3
                    else:
                        analysis['macd_signal'] = -0.5
                        if hist < 0:
                            analysis['macd_signal'] -= 0.3
            
            # Momento
            if 'momentum' in indicators and not pd.isna(indicators['momentum'][-1]):
                mom = indicators['momentum'][-1]
                analysis['momentum'] = np.clip(mom / 100, -1, 1)
            
            # Overall (média ponderada)
            analysis['overall'] = np.mean([
                analysis['rsi_signal'],
                analysis['macd_signal'] * 1.5,
                analysis['momentum'] * 0.8
            ])
            analysis['overall'] = np.clip(analysis['overall'], -1, 1)
            
        except Exception as e:
            logger.error(f"Erro na análise de momento: {e}")
        
        return analysis
    
    def _analyze_volatility(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """Análise de volatilidade"""
        analysis = {
            'level': 0.0,
            'regime': 'normal',
            'bollinger_signal': 0.0
        }
        
        try:
            # ATR
            if 'atr' in indicators and not pd.isna(indicators['atr'][-1]):
                atr = indicators['atr'][-1]
                avg_price = data['close'].mean()
                if avg_price > 0:
                    atr_pct = atr / avg_price
                    if atr_pct > 0.03:  # 3% = alta volatilidade
                        analysis['regime'] = 'high'
                        analysis['level'] = 1.0
                    elif atr_pct < 0.01:  # 1% = baixa volatilidade
                        analysis['regime'] = 'low'
                        analysis['level'] = 0.0
                    else:
                        analysis['regime'] = 'normal'
                        analysis['level'] = 0.5
            
            # Bollinger Bands
            if all(k in indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']):
                close = data['close'].values[-1] if len(data) > 0 else 0
                upper = indicators['bb_upper'][-1]
                lower = indicators['bb_lower'][-1]
                middle = indicators['bb_middle'][-1]
                
                if not pd.isna(upper) and not pd.isna(lower) and not pd.isna(middle):
                    bandwidth = (upper - lower) / middle if middle > 0 else 0
                    
                    # Posição do preço nas bandas
                    if close >= upper:
                        analysis['bollinger_signal'] = -0.3  # Bearish
                    elif close <= lower:
                        analysis['bollinger_signal'] = 0.3   # Bullish
                    else:
                        pos = (close - lower) / (upper - lower)
                        analysis['bollinger_signal'] = (pos - 0.5) * 0.4
                    
                    # Largura das bandas indica volatilidade
                    analysis['bandwidth'] = bandwidth
                    
        except Exception as e:
            logger.error(f"Erro na análise de volatilidade: {e}")
        
        return analysis
    
    def _analyze_price_action(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """Análise de Price Action"""
        analysis = {
            'candle_pattern': 'none',
            'pattern_strength': 0.0,
            'breakout': 0.0,
            'pullback': 0.0
        }
        
        try:
            # Padrões de candle
            if 'candle_pattern' in indicators:
                pattern = indicators['candle_pattern']
                if pattern and pattern != 'none':
                    analysis['candle_pattern'] = pattern
                    analysis['pattern_strength'] = 0.7
            
            # Suportes e resistências
            sr = self.support_resistance.find_levels(data)
            if sr:
                close = data['close'].values[-1]
                
                # Distância para suporte e resistência
                if sr.get('support'):
                    analysis['support_distance'] = abs(close - sr['support']) / close
                if sr.get('resistance'):
                    analysis['resistance_distance'] = abs(close - sr['resistance']) / close
                
                # Breakout
                if sr.get('resistance') and close > sr['resistance'] * 1.005:
                    analysis['breakout'] = 1.0
                elif sr.get('support') and close < sr['support'] * 0.995:
                    analysis['breakout'] = -1.0
            
            # Pullback (preço voltando para média)
            if 'ema_21' in indicators and not pd.isna(indicators['ema_21'][-1]):
                ema_21 = indicators['ema_21'][-1]
                close = data['close'].values[-1]
                deviation = (close - ema_21) / ema_21
                analysis['pullback'] = np.clip(-deviation * 5, -1, 1)
            
        except Exception as e:
            logger.error(f"Erro na análise de price action: {e}")
        
        return analysis
    
    def _analyze_volume(self, data: pd.DataFrame, is_otc: bool) -> Dict:
        """Análise de volume (adaptado para OTC)"""
        analysis = {
            'trend': 0.0,
            'spike': False,
            'confirmation': 0.0,
            'available': False
        }
        
        try:
            if 'volume' not in data.columns or data['volume'].sum() == 0:
                # OTC: sem volume real
                analysis['available'] = False
                # Usa comportamento estatístico dos preços
                close = data['close'].values
                if len(close) > 20:
                    returns = np.diff(np.log(close))
                    volatility = np.std(returns)
                    # "Volume" simulado pela volatilidade
                    if volatility > 0.01:
                        analysis['confirmation'] = 0.3
                    else:
                        analysis['confirmation'] = 0.0
                return analysis
            
            # Volume real disponível
            analysis['available'] = True
            volume = data['volume'].values
            close = data['close'].values
            
            # Volume SMA
            if 'volume_sma' in data:
                vol_sma = data['volume_sma'].values[-20:]
                current_vol = volume[-1]
                avg_vol = np.mean(vol_sma) if len(vol_sma) > 0 else 1
                
                if avg_vol > 0:
                    ratio = current_vol / avg_vol
                    if ratio > 1.5:
                        analysis['spike'] = True
                        analysis['confirmation'] = 1.0
                    else:
                        analysis['confirmation'] = ratio - 0.5
                
                # Tendência de volume
                if len(volume) > 10:
                    vol_slope = np.polyfit(range(10), volume[-10:], 1)[0]
                    analysis['trend'] = np.clip(vol_slope / (avg_vol + 1e-6), -1, 1)
            
        except Exception as e:
            logger.error(f"Erro na análise de volume: {e}")
        
        return analysis
    
    def _determine_context(self, data: pd.DataFrame, indicators: Dict, 
                          is_otc: bool) -> MarketContext:
        """Determina o contexto atual do mercado"""
        try:
            # OTC
            if is_otc:
                return MarketContext.OTC
            
            # ADX para identificar trending vs ranging
            if 'adx' in indicators and not pd.isna(indicators['adx'][-1]):
                adx = indicators['adx'][-1]
                
                # Volatilidade
                if 'atr' in indicators and not pd.isna(indicators['atr'][-1]):
                    avg_price = data['close'].mean()
                    if avg_price > 0:
                        atr_pct = indicators['atr'][-1] / avg_price
                        if atr_pct > 0.025:
                            return MarketContext.VOLATILE
                
                if adx > 30:
                    return MarketContext.TRENDING
                elif adx < 20:
                    return MarketContext.RANGING
                else:
                    return MarketContext.BREAKOUT
            
            return MarketContext.RANGING
            
        except Exception as e:
            logger.error(f"Erro ao determinar contexto: {e}")
            return MarketContext.RANGING
    
    def _assemble_factors(self, data: pd.DataFrame, indicators: Dict,
                         trend: Dict, momentum: Dict, volatility: Dict,
                         price_action: Dict, volume: Dict, context: MarketContext,
                         timeframe: str, is_otc: bool) -> AnalysisFactors:
        """Monta todos os fatores em um objeto"""
        
        factors = AnalysisFactors()
        
        # Tendência
        factors.trend_direction = trend.get('direction', 0.0)
        factors.trend_strength = trend.get('strength', 0.0)
        factors.ema_alignment = trend.get('alignment', 0.0)
        factors.vwap_position = trend.get('vwap_position', 0.0)
        
        # Momento
        factors.rsi_value = indicators.get('rsi', [50])[-1] if 'rsi' in indicators else 50
        factors.macd_signal = momentum.get('macd_signal', 0.0)
        factors.momentum = momentum.get('momentum', 0.0)
        factors.adx_value = indicators.get('adx', [25])[-1] if 'adx' in indicators else 25
        
        # Volatilidade
        if 'atr' in indicators:
            factors.atr_value = indicators['atr'][-1]
        factors.bollinger_position = volatility.get('bollinger_signal', 0.0)
        factors.bollinger_width = volatility.get('bandwidth', 0.0)
        factors.volatility_regime = volatility.get('regime', 'normal')
        
        # Price Action
        factors.candle_pattern = price_action.get('candle_pattern', 'none')
        factors.pattern_strength = price_action.get('pattern_strength', 0.0)
        factors.support_distance = price_action.get('support_distance', 0.0)
        factors.resistance_distance = price_action.get('resistance_distance', 0.0)
        factors.breakout_level = price_action.get('breakout', 0.0)
        factors.pullback_depth = price_action.get('pullback', 0.0)
        
        # Volume
        factors.volume_trend = volume.get('trend', 0.0)
        factors.volume_spike = volume.get('spike', False)
        factors.volume_confirmation = volume.get('confirmation', 0.0)
        
        # Contexto
        factors.market_context = context
        factors.timeframe = timeframe
        factors.is_otc = is_otc
        
        return factors
    
    def _calculate_category_scores(self, factors: AnalysisFactors) -> AnalysisFactors:
        """Calcula scores para cada categoria"""
        
        # Trend Score (baseado em direção, força e alinhamento)
        factors.trend_score = (
            factors.trend_direction * 0.4 +
            factors.trend_strength * 0.3 +
            factors.ema_alignment * 0.3
        )
        factors.trend_score = np.clip(factors.trend_score, -1, 1)
        
        # Momentum Score
        factors.momentum_score = (
            ((factors.rsi_value - 50) / 50) * 0.3 +
            factors.macd_signal * 0.4 +
            factors.momentum * 0.3
        )
        factors.momentum_score = np.clip(factors.momentum_score, -1, 1)
        
        # Volatility Score
        if factors.volatility_regime == 'high':
            vol_factor = 0.5
        elif factors.volatility_regime == 'low':
            vol_factor = -0.2
        else:
            vol_factor = 0.0
        
        factors.volatility_score = vol_factor + factors.bollinger_position * 0.5
        factors.volatility_score = np.clip(factors.volatility_score, -1, 1)
        
        # Price Action Score
        factors.price_action_score = (
            factors.pattern_strength * 0.3 +
            factors.breakout_level * 0.4 +
            factors.pullback_depth * 0.3
        )
        factors.price_action_score = np.clip(factors.price_action_score, -1, 1)
        
        # Volume Score
        factors.volume_score = factors.volume_confirmation * 0.6 + factors.volume_trend * 0.4
        factors.volume_score = np.clip(factors.volume_score, -1, 1)
        
        # Context Score
        context_scores = {
            MarketContext.TRENDING: 1.0,
            MarketContext.BREAKOUT: 0.8,
            MarketContext.VOLATILE: 0.5,
            MarketContext.RANGING: 0.3,
            MarketContext.OTC: 0.2
        }
        factors.context_score = context_scores.get(factors.market_context, 0.3)
        
        return factors
    
    def _calculate_confidence(self, factors: AnalysisFactors) -> AnalysisFactors:
        """Calcula o confidence score final"""
        
        # Combinação ponderada dos scores
        weighted_score = (
            factors.trend_score * self.weights['trend'] +
            factors.momentum_score * self.weights['momentum'] +
            factors.price_action_score * self.weights['price_action'] +
            factors.volatility_score * self.weights['volatility'] +
            factors.volume_score * self.weights['volume'] +
            factors.context_score * self.weights['context']
        )
        
        # Ajuste para OTC
        if factors.is_otc:
            weighted_score *= 0.85  # Reduz confiança em OTC
        
        # Converte para 0-1
        confidence = (weighted_score + 1) / 2
        confidence = np.clip(confidence, 0.0, 1.0)
        
        # Multiplicador baseado na força da tendência
        if abs(factors.trend_direction) > 0.5:
            confidence = min(1.0, confidence * 1.1)
        
        factors.confidence = confidence
        
        # Determina tipo de sinal
        if weighted_score > 0.15:
            factors.signal_type = SignalType.CALL
        elif weighted_score < -0.15:
            factors.signal_type = SignalType.PUT
        else:
            factors.signal_type = SignalType.NEUTRAL
        
        return factors
    
    def _generate_signal(self, symbol: str, timeframe: str, 
                         factors: AnalysisFactors) -> Signal:
        """Gera objeto Signal a partir dos fatores"""
        
        # Força do sinal baseado na confiança
        if factors.confidence >= 0.8:
            strength = SignalStrength.STRONG
        elif factors.confidence >= 0.6:
            strength = SignalStrength.MEDIUM
        else:
            strength = SignalStrength.WEAK
        
        # Lista de razões (será preenchida pelo explainer)
        reasons = factors.reasons if factors.reasons else [
            f"Confiança: {factors.confidence:.1%}"
        ]
        
        # Gera metadados
        metadata = {
            'trend_score': factors.trend_score,
            'momentum_score': factors.momentum_score,
            'price_action_score': factors.price_action_score,
            'volatility_score': factors.volatility_score,
            'volume_score': factors.volume_score,
            'context_score': factors.context_score,
            'market_context': factors.market_context.value,
            'timeframe': timeframe,
            'is_otc': factors.is_otc,
            'candle_pattern': factors.candle_pattern,
            'rsi': factors.rsi_value,
            'adx': factors.adx_value,
            'breakout': factors.breakout_level,
            'pullback': factors.pullback_depth
        }
        
        signal = Signal(
            symbol=symbol,
            signal_type=factors.signal_type or SignalType.NEUTRAL,
            confidence=factors.confidence,
            strength=strength,
            timestamp=datetime.now(),
            timeframe=timeframe,
            reasons=reasons,
            metadata=metadata
        )
        
        return signal
    
    def _add_explanation(self, signal: Signal, factors: AnalysisFactors) -> Signal:
        """Adiciona explicação detalhada ao sinal"""
        
        reasons = []
        
        # Tendência
        if abs(factors.trend_direction) > 0.3:
            direction = "bullish" if factors.trend_direction > 0 else "bearish"
            strength = "forte" if factors.trend_strength > 0.5 else "moderada"
            reasons.append(f"✓ Tendência {direction} ({strength})")
        
        # Alinhamento EMAs
        if abs(factors.ema_alignment) > 0.5:
            direction = "bullish" if factors.ema_alignment > 0 else "bearish"
            reasons.append(f"✓ EMAs alinhadas ({direction})")
        
        # RSI
        if factors.rsi_value > 70:
            reasons.append(f"✓ RSI sobrecomprado ({factors.rsi_value:.1f})")
        elif factors.rsi_value < 30:
            reasons.append(f"✓ RSI sobrevendido ({factors.rsi_value:.1f})")
        elif 40 < factors.rsi_value < 60:
            reasons.append(f"✓ RSI neutro ({factors.rsi_value:.1f})")
        
        # MACD
        if abs(factors.macd_signal) > 0.3:
            direction = "bullish" if factors.macd_signal > 0 else "bearish"
            reasons.append(f"✓ MACD {direction}")
        
        # Candle Pattern
        if factors.candle_pattern != 'none':
            reasons.append(f"✓ Padrão: {factors.candle_pattern}")
        
        # Breakout
        if abs(factors.breakout_level) > 0.5:
            direction = "rompimento alta" if factors.breakout_level > 0 else "rompimento baixa"
            reasons.append(f"✓ {direction}")
        
        # Pullback
        if abs(factors.pullback_depth) > 0.3:
            direction = "pullback de alta" if factors.pullback_depth > 0 else "pullback de baixa"
            reasons.append(f"✓ {direction}")
        
        # Volume
        if factors.volume_spike:
            reasons.append("✓ Pico de volume confirmando")
        elif abs(factors.volume_confirmation) > 0.3:
            direction = "alta" if factors.volume_confirmation > 0 else "baixa"
            reasons.append(f"✓ Volume em {direction}")
        
        # Contexto
        if factors.market_context == MarketContext.TRENDING:
            reasons.append("✓ Mercado em tendência")
        elif factors.market_context == MarketContext.BREAKOUT:
            reasons.append("✓ Zona de rompimento")
        elif factors.market_context == MarketContext.VOLATILE:
            reasons.append("⚠ Mercado volátil")
        
        # Adiciona confiança
        reasons.append(f"📊 Score: {factors.confidence:.1%}")
        
        signal.reasons = reasons
        signal.metadata['reasons'] = reasons
        
        return signal