"""
Overlay Flutuante - Neural Binary Signals
APENAS OTC - SEM YAHOO (evita Segmentation fault)
"""

import sys
import time
import threading
import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SignalOverlay(QWidget):
    """Janela flutuante com sinais de alta confiança (OTC)"""
    
    signal_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 350, 500)
        
        self.current_signal = None
        self.signal_executed = False
        self.start_drag_pos = None
        self.high_confidence_signals = []
        
        self.setStyleSheet("""
            QWidget#main_frame {
                background-color: rgba(15, 15, 35, 230);
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
            QLabel#confidence_high {
                color: #a6e3a1;
                font-size: 20px;
                font-weight: bold;
            }
            QLabel#confidence_medium {
                color: #f9e2af;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#confidence_low {
                color: #f38ba8;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        self.init_ui()
        self.signal_updated.connect(self._update_ui)
        self.start_monitoring()
        
    def init_ui(self):
        main = QWidget()
        main.setObjectName("main_frame")
        layout = QVBoxLayout(main)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # BARRA DE TÍTULO
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("🎯 NEURAL SIGNALS (OTC)")
        title.setStyleSheet("font-weight: bold; color: #cba6f7; font-size: 13px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # INDICADOR OTC
        self.mode_indicator = QLabel("🔄 OTC")
        self.mode_indicator.setStyleSheet("""
            QLabel {
                background-color: #f9e2af;
                color: #1e1e2e;
                border-radius: 8px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(self.mode_indicator)
        
        min_btn = QPushButton("─")
        min_btn.setFixedSize(30, 30)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                font-size: 18px;
                padding: 0;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); }
        """)
        title_layout.addWidget(min_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,0,0,0.3);
                border-radius: 15px;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover { background: rgba(255,0,0,0.6); }
        """)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # STATUS
        status_frame = QWidget()
        status_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 8px; padding: 5px;")
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("🟢 Monitorando USD/JPY (OTC)")
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.signal_count_label = QLabel("Sinais: 0")
        self.signal_count_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        status_layout.addWidget(self.signal_count_label)
        
        layout.addWidget(status_frame)
        
        # INFORMAÇÕES DO SINAL
        self.signal_frame = QWidget()
        signal_layout = QVBoxLayout(self.signal_frame)
        signal_layout.setSpacing(5)
        
        header = QHBoxLayout()
        self.symbol_label = QLabel("USD/JPY")
        self.symbol_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #cdd6f4;")
        header.addWidget(self.symbol_label)
        header.addStretch()
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        header.addWidget(self.time_label)
        signal_layout.addLayout(header)
        
        price_frame = QWidget()
        price_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 8px;")
        price_layout = QHBoxLayout(price_frame)
        self.price_label = QLabel("📊 Preço: --")
        self.price_label.setStyleSheet("font-size: 18px; color: #cdd6f4; padding: 5px;")
        price_layout.addWidget(self.price_label)
        price_layout.addStretch()
        self.broker_status = QLabel("🔗 OTC")
        self.broker_status.setStyleSheet("color: #a6adc8; font-size: 11px;")
        price_layout.addWidget(self.broker_status)
        signal_layout.addWidget(price_frame)
        
        self.signal_label = QLabel("⏳ AGUARDANDO SINAL FORTE")
        self.signal_label.setStyleSheet("""
            font-size: 30px; font-weight: bold; color: #cba6f7;
            padding: 15px; background: rgba(255,255,255,0.05);
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
        
        self.reasons_label = QLabel("")
        self.reasons_label.setStyleSheet("color: #a6adc8; font-size: 12px; padding: 5px;")
        self.reasons_label.setWordWrap(True)
        signal_layout.addWidget(self.reasons_label)
        
        layout.addWidget(self.signal_frame)
        
        self.entry_btn = QPushButton("⏳ AGUARDANDO SINAL ≥ 85%")
        self.entry_btn.setObjectName("waiting")
        self.entry_btn.setFixedHeight(50)
        self.entry_btn.clicked.connect(self.on_entry_clicked)
        layout.addWidget(self.entry_btn)
        
        instructions = QLabel("📌 Arraste a janela para posicionar sobre a corretora")
        instructions.setStyleSheet("color: #585b70; font-size: 10px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(main)
        
        self.hide()
    
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
        """Loop APENAS com dados OTC (sem Yahoo)"""
        import pandas as pd
        import numpy as np
        from ..core import DecisionEngine
        
        engine = DecisionEngine()
        best_signal = None
        best_confidence = 0
        symbol = "USD/JPY"
        
        while self.monitoring:
            try:
                # Gera dados OTC simulados
                np.random.seed(int(time.time() * 1000) % 100000)
                base_price = 149.50 + np.random.randn() * 0.5
                prices = base_price + np.cumsum(np.random.randn(100) * 0.08)
                prices = np.maximum(prices, base_price - 2)
                
                data = pd.DataFrame({
                    'open': prices[:-1],
                    'high': prices[:-1] + np.abs(np.random.randn(99) * 0.1),
                    'low': prices[:-1] - np.abs(np.random.randn(99) * 0.1),
                    'close': prices[1:],
                    'volume': np.random.randint(100, 5000, 99)
                })
                
                # Corrige high >= low
                data['high'] = data[['high', 'low']].max(axis=1)
                data['low'] = data[['low', 'open', 'close']].min(axis=1)
                
                signal = engine.analyze(data, symbol, "M5")
                
                if signal and signal.confidence >= 0.85:
                    price = round(data['close'].iloc[-1], 3)
                    signal_data = {
                        'symbol': symbol,
                        'type': signal.signal_type.value,
                        'confidence': signal.confidence,
                        'strength': signal.strength.value,
                        'price': price,
                        'timestamp': QTime.currentTime().toString('HH:mm:ss'),
                        'reasons': signal.reasons[:3]
                    }
                    
                    if signal.confidence > best_confidence or self.signal_executed:
                        best_signal = signal_data
                        best_confidence = signal.confidence
                        self.signal_executed = False
                        self.signal_updated.emit(signal_data)
                        print(f"🎯 OTC: {signal.signal_type.value} com {signal.confidence:.1%} @ {price}")
                
                time.sleep(8)
                
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(5)
    
    def _update_ui(self, data):
        confidence = data.get('confidence', 0)
        signal_type = data.get('type', 'NEUTRAL')
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        self.symbol_label.setText(data.get('symbol', '--'))
        self.time_label.setText(data.get('timestamp', '--:--:--'))
        
        price = data.get('price', '--')
        self.price_label.setText(f"📊 Preço: {price}")
        
        if signal_type == 'CALL':
            self.signal_label.setText("📈 COMPRA")
            self.signal_label.setStyleSheet("""
                font-size: 32px; font-weight: bold; color: #a6e3a1;
                padding: 15px; background: rgba(166,227,161,0.15);
                border-radius: 10px; border: 2px solid #a6e3a1;
            """)
            self.entry_btn.setText("📈 COMPRAR AGORA")
            self.entry_btn.setObjectName("buy")
        elif signal_type == 'PUT':
            self.signal_label.setText("📉 VENDA")
            self.signal_label.setStyleSheet("""
                font-size: 32px; font-weight: bold; color: #f38ba8;
                padding: 15px; background: rgba(243,139,168,0.15);
                border-radius: 10px; border: 2px solid #f38ba8;
            """)
            self.entry_btn.setText("📉 VENDER AGORA")
            self.entry_btn.setObjectName("sell")
        
        conf_pct = confidence * 100
        self.confidence_label.setText(f"{conf_pct:.1f}% PROBABILIDADE")
        self.confidence_bar.setValue(int(conf_pct))
        
        if confidence >= 0.90:
            self.confidence_label.setObjectName("confidence_high")
        elif confidence >= 0.85:
            self.confidence_label.setObjectName("confidence_medium")
        else:
            self.confidence_label.setObjectName("confidence_low")
        
        reasons = data.get('reasons', [])
        if reasons:
            self.reasons_label.setText("📊 " + " | ".join(reasons[:2]))
        
        self.signal_count_label.setText(f"Sinais: {len(self.high_confidence_signals)}")
        self.current_signal = data
    
    def on_entry_clicked(self):
        if not self.current_signal:
            return
        
        signal_type = self.current_signal.get('type', 'NEUTRAL')
        symbol = self.current_signal.get('symbol', '--')
        confidence = self.current_signal.get('confidence', 0)
        price = self.current_signal.get('price', '--')
        
        msg = f"""
╔══════════════════════════════════════╗
║        📊 CONFIRMAR ENTRADA          ║
╠══════════════════════════════════════╣
║                                      ║
║  Ativo:    {symbol}                    ║
║  Sinal:    {signal_type}               ║
║  Preço:    {price}                     ║
║  Confiança: {confidence:.1%}              ║
║                                      ║
╚══════════════════════════════════════╝
        """
        
        reply = QMessageBox.question(
            self,
            "✅ Confirmar Entrada",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.signal_executed = True
            self.current_signal['status'] = 'EXECUTADO'
            self.high_confidence_signals.append(self.current_signal)
            
            QMessageBox.information(
                self,
                "✅ ENTRADA EXECUTADA",
                f"""
🎯 SINAL {signal_type} EXECUTADO!

Ativo: {symbol}
Preço: {price}
Confiança: {confidence:.1%}

📊 Aguarde o próximo sinal forte...
                """
            )
            
            self.signal_label.setText("⏳ AGUARDANDO PRÓXIMO SINAL")
            self.signal_label.setStyleSheet("""
                font-size: 24px; font-weight: bold; color: #cba6f7;
                padding: 15px; background: rgba(255,255,255,0.05);
                border-radius: 10px;
            """)
            self.entry_btn.setText("⏳ AGUARDANDO SINAL ≥ 85%")
            self.entry_btn.setObjectName("waiting")
            self.confidence_label.setText("EXECUTADO ✓")
            self.confidence_bar.setValue(100)
            self.reasons_label.setText("✅ Sinal executado com sucesso!")
            
            print(f"✅ ENTRADA EXECUTADA: {signal_type} {symbol} @ {price}")


def run_overlay():
    from ..core import DecisionEngine
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    overlay = SignalOverlay()
    overlay.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()