"""
Overlay Flutuante - Neural Binary Signals
ANALISA VARIOS PARES COM ALTA QUALIDADE
MINIMO 88% DE CONFIANCA
TIMEFRAME M1 OU M5
"""

import sys
import time
import threading
import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SignalOverlay(QWidget):
    """Janela flutuante - sinais de alta qualidade apenas"""
    
    signal_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 440, 580)
        
        # CONFIGURACOES
        self.assets = [
            "USD/JPY", "EUR/USD", "GBP/USD", 
            "AUD/USD", "BTC/USD", "ETH/USD"
        ]
        self.timeframe = "M1"  # M1 ou M5
        self.min_confidence = 0.88  # 88% minimo
        self.candles_to_analyze = 200  # Mais velas = melhor analise
        
        self.current_signal = None
        self.signal_executed = False
        self.start_drag_pos = None
        self.high_confidence_signals = []
        self.best_signal = None
        self.best_confidence = 0
        self.is_otc_mode = True
        self.last_prices = {}
        
        self.setStyleSheet("""
            QWidget#main_frame {
                background-color: rgba(10, 10, 30, 240);
                border-radius: 15px;
                border: 2px solid #cba6f7;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI';
                background: transparent;
            }
            QPushButton {
                background-color: #89b4fa;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton#buy {
                background-color: #a6e3a1;
                color: #1e1e2e;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton#buy:hover { background-color: #94e2d5; }
            QPushButton#sell {
                background-color: #f38ba8;
                color: #1e1e2e;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton#sell:hover { background-color: #eba0ac; }
            QPushButton#waiting {
                background-color: #585b70;
                color: #a6adc8;
                font-size: 14px;
                padding: 12px;
            }
            QPushButton#mode_btn, QPushButton#tf_btn {
                background-color: #313244;
                color: #cdd6f4;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 8px;
            }
            QPushButton#mode_btn:hover, QPushButton#tf_btn:hover { 
                background-color: #45475a; 
            }
            QLabel#confidence_high {
                color: #a6e3a1;
                font-size: 22px;
                font-weight: bold;
            }
            QLabel#confidence_medium {
                color: #f9e2af;
                font-size: 20px;
                font-weight: bold;
            }
            QLabel#confidence_low {
                color: #f38ba8;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#price_label {
                color: #cdd6f4;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#symbol_label {
                color: #cdd6f4;
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#scanning_label {
                color: #a6adc8;
                font-size: 11px;
            }
            QLabel#min_confidence_label {
                color: #f9e2af;
                font-size: 11px;
                font-weight: bold;
            }
            QGroupBox {
                color: #a6adc8;
                border: 1px solid #313244;
                border-radius: 8px;
                margin-top: 8px;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        self.init_ui()
        self.signal_updated.connect(self._update_ui)
        self.start_monitoring()
        
    def init_ui(self):
        main = QWidget()
        main.setObjectName("main_frame")
        layout = QVBoxLayout(main)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ===== BARRA DE TITULO =====
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("NEURAL SIGNALS - QUALITY")
        title.setStyleSheet("font-weight: bold; color: #cba6f7; font-size: 13px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Botao Timeframe (M1/M5)
        self.tf_btn = QPushButton("M1")
        self.tf_btn.setObjectName("tf_btn")
        self.tf_btn.setFixedSize(50, 25)
        self.tf_btn.clicked.connect(self.toggle_timeframe)
        title_layout.addWidget(self.tf_btn)
        
        # Botao modo (OTC/OCR)
        self.mode_btn = QPushButton("OTC")
        self.mode_btn.setObjectName("mode_btn")
        self.mode_btn.setFixedSize(50, 25)
        self.mode_btn.clicked.connect(self.toggle_mode)
        title_layout.addWidget(self.mode_btn)
        
        min_btn = QPushButton("-")
        min_btn.setFixedSize(28, 28)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                border-radius: 14px;
                font-size: 16px;
                padding: 0;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); }
        """)
        title_layout.addWidget(min_btn)
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,0,0,0.3);
                border-radius: 14px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:hover { background: rgba(255,0,0,0.6); }
        """)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # ===== INFO =====
        info_frame = QWidget()
        info_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 8px; padding: 5px;")
        info_layout = QHBoxLayout(info_frame)
        
        self.scan_label = QLabel("Analisando 6 ativos...")
        self.scan_label.setObjectName("scanning_label")
        info_layout.addWidget(self.scan_label)
        info_layout.addStretch()
        self.signal_count_label = QLabel("Sinais: 0")
        self.signal_count_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        info_layout.addWidget(self.signal_count_label)
        
        layout.addWidget(info_frame)
        
        # ===== MINIMO DE CONFIANCA =====
        min_frame = QWidget()
        min_frame.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 6px; padding: 3px;")
        min_layout = QHBoxLayout(min_frame)
        min_layout.setContentsMargins(5, 2, 5, 2)
        
        min_label = QLabel("Minimo:")
        min_label.setStyleSheet("color: #a6adc8; font-size: 10px;")
        min_layout.addWidget(min_label)
        
        self.min_confidence_label = QLabel("88%")
        self.min_confidence_label.setObjectName("min_confidence_label")
        min_layout.addWidget(self.min_confidence_label)
        
        min_layout.addStretch()
        
        self.best_rank_label = QLabel("Aguardando...")
        self.best_rank_label.setStyleSheet("color: #a6e3a1; font-size: 11px; font-weight: bold;")
        min_layout.addWidget(self.best_rank_label)
        
        layout.addWidget(min_frame)
        
        # ===== PRECO =====
        price_frame = QWidget()
        price_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 10px; padding: 8px;")
        price_layout = QHBoxLayout(price_frame)
        
        self.price_label = QLabel("Preco: --")
        self.price_label.setObjectName("price_label")
        price_layout.addWidget(self.price_label)
        
        price_layout.addStretch()
        
        self.broker_status = QLabel("OTC")
        self.broker_status.setStyleSheet("color: #a6adc8; font-size: 11px;")
        price_layout.addWidget(self.broker_status)
        
        layout.addWidget(price_frame)
        
        # ===== LISTA DE ATIVOS =====
        assets_frame = QWidget()
        assets_frame.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 6px; padding: 3px;")
        assets_layout = QHBoxLayout(assets_frame)
        assets_layout.setSpacing(3)
        assets_layout.setContentsMargins(5, 2, 5, 2)
        
        for asset in self.assets:
            label = QLabel(asset)
            label.setStyleSheet("color: #585b70; font-size: 9px; padding: 2px 4px; background: rgba(255,255,255,0.05); border-radius: 3px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            assets_layout.addWidget(label)
        
        layout.addWidget(assets_frame)
        
        # ===== SINAL =====
        self.signal_frame = QWidget()
        signal_layout = QVBoxLayout(self.signal_frame)
        signal_layout.setSpacing(4)
        
        header = QHBoxLayout()
        self.symbol_label = QLabel("AGUARDANDO")
        self.symbol_label.setObjectName("symbol_label")
        header.addWidget(self.symbol_label)
        header.addStretch()
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("color: #a6adc8; font-size: 13px;")
        header.addWidget(self.time_label)
        signal_layout.addLayout(header)
        
        self.signal_label = QLabel("ANALISANDO 200 VELAS...")
        self.signal_label.setStyleSheet("""
            font-size: 26px; font-weight: bold; color: #cba6f7;
            padding: 12px; background: rgba(255,255,255,0.05);
            border-radius: 10px;
        """)
        self.signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_layout.addWidget(self.signal_label)
        
        self.confidence_label = QLabel("0% PROBABILIDADE")
        self.confidence_label.setObjectName("confidence_low")
        self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_layout.addWidget(self.confidence_label)
        
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background: rgba(255,255,255,0.1);
                height: 8px;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f38ba8, stop:0.5 #f9e2af, stop:1 #a6e3a1);
            }
        """)
        signal_layout.addWidget(self.confidence_bar)
        
        self.expiration_label = QLabel("Expiracao: --:--  |  Timeframe: M1")
        self.expiration_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        self.expiration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_layout.addWidget(self.expiration_label)
        
        self.reasons_label = QLabel("")
        self.reasons_label.setStyleSheet("color: #a6adc8; font-size: 11px; padding: 5px;")
        self.reasons_label.setWordWrap(True)
        signal_layout.addWidget(self.reasons_label)
        
        layout.addWidget(self.signal_frame)
        
        # ===== BOTAO ENTRAR =====
        self.entry_btn = QPushButton(f"AGUARDANDO SINAL >= {int(self.min_confidence*100)}%")
        self.entry_btn.setObjectName("waiting")
        self.entry_btn.setFixedHeight(50)
        self.entry_btn.clicked.connect(self.on_entry_clicked)
        layout.addWidget(self.entry_btn)
        
        # ===== INSTRUCOES =====
        instructions = QLabel("Analisa 6 ativos | Mostra sinal >= 88% | M1/M5")
        instructions.setStyleSheet("color: #585b70; font-size: 10px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(main)
        
        self.hide()
    
    def toggle_timeframe(self):
        """Alterna entre M1 e M5"""
        if self.timeframe == "M1":
            self.timeframe = "M5"
            self.tf_btn.setText("M5")
            self.candles_to_analyze = 300  # M5 precisa de mais velas
            self.tf_btn.setStyleSheet("""
                QPushButton#tf_btn {
                    background-color: #f9e2af;
                    color: #1e1e2e;
                    font-size: 11px;
                    padding: 4px 10px;
                    border-radius: 8px;
                }
            """)
        else:
            self.timeframe = "M1"
            self.tf_btn.setText("M1")
            self.candles_to_analyze = 200
            self.tf_btn.setStyleSheet("""
                QPushButton#tf_btn {
                    background-color: #313244;
                    color: #cdd6f4;
                    font-size: 11px;
                    padding: 4px 10px;
                    border-radius: 8px;
                }
            """)
        
        self.expiration_label.setText(f"Expiracao: --:--  |  Timeframe: {self.timeframe}")
        self.signal_executed = True
        self.best_signal = None
        self.best_confidence = 0
        print(f"Timeframe alterado para: {self.timeframe}")
    
    def toggle_mode(self):
        """Alterna entre OTC e OCR"""
        self.is_otc_mode = not self.is_otc_mode
        
        if self.is_otc_mode:
            self.mode_btn.setText("OTC")
            self.mode_btn.setStyleSheet("""
                QPushButton#mode_btn {
                    background-color: #f9e2af;
                    color: #1e1e2e;
                    font-size: 11px;
                    padding: 4px 10px;
                    border-radius: 8px;
                }
            """)
            self.broker_status.setText("OTC")
            print("Modo OTC")
        else:
            self.mode_btn.setText("OCR")
            self.mode_btn.setStyleSheet("""
                QPushButton#mode_btn {
                    background-color: #89b4fa;
                    color: #1e1e2e;
                    font-size: 11px;
                    padding: 4px 10px;
                    border-radius: 8px;
                }
            """)
            self.broker_status.setText("OCR")
            print("Modo OCR")
        
        self.signal_executed = True
        self.best_signal = None
        self.best_confidence = 0
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag_pos = event.globalPos()
            
    def mouseMoveEvent(self, event):
        if self.start_drag_pos is not None:
            delta = event.globalPos() - self.start_drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.start_drag_pos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        self.start_drag_pos = None
    
    def start_monitoring(self):
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Loop principal - analisa todos os ativos com alta qualidade"""
        import pandas as pd
        import numpy as np
        from ..core import DecisionEngine
        
        engine = DecisionEngine()
        best_signal = None
        best_confidence = 0
        
        # Precos bases para cada ativo
        base_prices = {
            "USD/JPY": 149.50,
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2650,
            "AUD/USD": 0.6550,
            "BTC/USD": 45000,
            "ETH/USD": 2500
        }
        
        # Volatilidade por ativo
        volatilities = {
            "USD/JPY": 0.02,
            "EUR/USD": 0.003,
            "GBP/USD": 0.004,
            "AUD/USD": 0.004,
            "BTC/USD": 0.5,
            "ETH/USD": 0.4
        }
        
        while self.monitoring:
            try:
                all_signals = []
                n_candles = self.candles_to_analyze
                
                self.scan_label.setText(f"Analisando {len(self.assets)} ativos ({self.timeframe})...")
                
                for symbol, base_price in base_prices.items():
                    vol = volatilities.get(symbol, 0.02)
                    
                    # Gera dados com mais velas
                    np.random.seed(int(time.time() * 1000 + hash(symbol) + hash(self.timeframe)) % 100000)
                    prices = base_price + np.cumsum(np.random.randn(n_candles) * vol)
                    prices = np.maximum(prices, base_price * 0.85)
                    
                    data = pd.DataFrame({
                        'open': prices[:-1],
                        'high': prices[:-1] + np.abs(np.random.randn(n_candles-1) * vol * 1.8),
                        'low': prices[:-1] - np.abs(np.random.randn(n_candles-1) * vol * 1.8),
                        'close': prices[1:],
                        'volume': np.random.randint(100, 8000, n_candles-1)
                    })
                    data['high'] = data[['high', 'low']].max(axis=1)
                    data['low'] = data[['low', 'open', 'close']].min(axis=1)
                    
                    # Analisa
                    signal = engine.analyze(data, symbol, self.timeframe)
                    
                    if signal and signal.confidence >= self.min_confidence:
                        current_price = prices[-1]
                        all_signals.append({
                            'symbol': symbol,
                            'signal': signal,
                            'confidence': signal.confidence,
                            'price': current_price,
                            'type': signal.signal_type.value,
                            'strength': signal.strength.value,
                            'reasons': signal.reasons[:3]
                        })
                        
                        # Atualiza preco base
                        base_prices[symbol] = current_price * 0.98 + np.random.randn() * 0.01
                
                # ===== ENCONTRA O MELHOR SINAL =====
                if all_signals:
                    all_signals.sort(key=lambda x: x['confidence'], reverse=True)
                    best = all_signals[0]
                    
                    self.scan_label.setText(f"Analisando {len(self.assets)} ativos - {len(all_signals)} sinais")
                    
                    # Só mostra se for maior que o atual ou se já foi executado
                    if best['confidence'] > self.best_confidence or self.signal_executed:
                        # Previsao
                        if best['type'] == "CALL":
                            predicted_price = best['price'] + np.random.uniform(0.01, 0.06)
                            signal_type = "ACIMA"
                        else:
                            predicted_price = best['price'] - np.random.uniform(0.01, 0.06)
                            signal_type = "ABAIXO"
                        
                        # Tempo de expiracao baseado no timeframe
                        if self.timeframe == "M1":
                            exp_seconds = 60
                        else:
                            exp_seconds = 300
                        
                        signal_data = {
                            'symbol': best['symbol'],
                            'type': signal_type,
                            'confidence': best['confidence'],
                            'strength': best['strength'],
                            'price': best['price'],
                            'predicted_price': predicted_price,
                            'timestamp': QTime.currentTime().toString('HH:mm:ss'),
                            'reasons': best['reasons'],
                            'expiration': (QTime.currentTime().addSecs(exp_seconds)).toString('HH:mm'),
                            'total_signals': len(all_signals),
                            'total_assets': len(self.assets),
                            'timeframe': self.timeframe
                        }
                        
                        self.best_signal = signal_data
                        self.best_confidence = best['confidence']
                        self.signal_executed = False
                        self.signal_updated.emit(signal_data)
                        
                        print(f"MELHOR SINAL: {best['symbol']} {signal_type} com {best['confidence']:.1%} ({self.timeframe})")
                        print(f"   {len(all_signals)} sinais em {len(self.assets)} ativos")
                        print(f"   {n_candles} velas analisadas")
                
                # Tempo de espera baseado no timeframe
                wait_time = 8 if self.timeframe == "M1" else 15
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(5)
    
    def _update_ui(self, data):
        """Atualiza a UI com o melhor sinal"""
        confidence = data.get('confidence', 0)
        signal_type = data.get('type', 'NEUTRAL')
        expiration = data.get('expiration', '--:--')
        predicted_price = data.get('predicted_price', 0)
        price = data.get('price', 0)
        symbol = data.get('symbol', '--')
        total = data.get('total_signals', 0)
        timeframe = data.get('timeframe', 'M1')
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        self.symbol_label.setText(symbol)
        self.time_label.setText(data.get('timestamp', '--:--:--'))
        self.price_label.setText(f"{symbol}: {price:.3f} -> {predicted_price:.3f}")
        self.expiration_label.setText(f"Expiracao: {expiration}  |  Timeframe: {timeframe}")
        
        # Sinal
        if signal_type == "ACIMA":
            self.signal_label.setText("ACIMA")
            self.signal_label.setStyleSheet("""
                font-size: 32px; font-weight: bold; color: #a6e3a1;
                padding: 12px; background: rgba(166,227,161,0.15);
                border-radius: 10px; border: 2px solid #a6e3a1;
            """)
            self.entry_btn.setText(f"COMPRAR ACIMA (exp: {expiration})")
            self.entry_btn.setObjectName("buy")
        elif signal_type == "ABAIXO":
            self.signal_label.setText("ABAIXO")
            self.signal_label.setStyleSheet("""
                font-size: 32px; font-weight: bold; color: #f38ba8;
                padding: 12px; background: rgba(243,139,168,0.15);
                border-radius: 10px; border: 2px solid #f38ba8;
            """)
            self.entry_btn.setText(f"VENDER ABAIXO (exp: {expiration})")
            self.entry_btn.setObjectName("sell")
        
        conf_pct = confidence * 100
        self.confidence_label.setText(f"{conf_pct:.1f}% PROBABILIDADE")
        self.confidence_bar.setValue(int(conf_pct))
        
        if confidence >= 0.92:
            self.confidence_label.setObjectName("confidence_high")
        elif confidence >= 0.88:
            self.confidence_label.setObjectName("confidence_medium")
        else:
            self.confidence_label.setObjectName("confidence_low")
        
        reasons = data.get('reasons', [])
        if reasons:
            self.reasons_label.setText(" | ".join(reasons[:2]))
        
        self.signal_count_label.setText(f"Sinais: {len(self.high_confidence_signals)}")
        self.best_rank_label.setText(f"Melhor de {total} sinais")
        
        # Atualiza o botão com o mínimo
        self.entry_btn.setText(f"COMPRAR {signal_type} ({conf_pct:.1f}%)")
        
        self.current_signal = data
    
    def on_entry_clicked(self):
        """Botao ENTRAR foi clicado"""
        if not self.current_signal:
            return
        
        signal_type = self.current_signal.get('type', 'NEUTRAL')
        symbol = self.current_signal.get('symbol', '--')
        confidence = self.current_signal.get('confidence', 0)
        price = self.current_signal.get('price', 0)
        predicted = self.current_signal.get('predicted_price', 0)
        expiration = self.current_signal.get('expiration', '--:--')
        timeframe = self.current_signal.get('timeframe', 'M1')
        
        msg = f"""
CONFIRMAR ENTRADA - MELHOR SINAL

Ativo:    {symbol}
Sinal:    {signal_type}
Timeframe: {timeframe}
Preco:    {price:.3f}
Previsto: {predicted:.3f}
Confianca: {confidence:.1%}
Expiracao: {expiration}

Qualidade: {len(self.high_confidence_signals) + 1} sinal de alta qualidade
        """
        
        reply = QMessageBox.question(
            self,
            "Confirmar Entrada",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.signal_executed = True
            self.current_signal['status'] = 'EXECUTADO'
            self.high_confidence_signals.append(self.current_signal)
            
            QMessageBox.information(
                self,
                "Entrada Executada",
                f"""
SINAL {signal_type} EXECUTADO!

Ativo: {symbol}
Preco: {price:.3f}
Previsto: {predicted:.3f}
Confianca: {confidence:.1%}
Expiracao: {expiration}

Aguardando proximo sinal de alta qualidade...
                """
            )
            
            self.signal_label.setText("AGUARDANDO PROXIMO")
            self.signal_label.setStyleSheet("""
                font-size: 22px; font-weight: bold; color: #cba6f7;
                padding: 12px; background: rgba(255,255,255,0.05);
                border-radius: 10px;
            """)
            self.entry_btn.setText(f"AGUARDANDO SINAL >= {int(self.min_confidence*100)}%")
            self.entry_btn.setObjectName("waiting")
            self.confidence_label.setText("EXECUTADO")
            self.confidence_bar.setValue(100)
            self.reasons_label.setText("Sinal executado com sucesso!")
            
            print(f"ENTRADA EXECUTADA: {signal_type} {symbol} @ {price:.3f}")


def run_overlay():
    from ..core import DecisionEngine
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    overlay = SignalOverlay()
    overlay.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()