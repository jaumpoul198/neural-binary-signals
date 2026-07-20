"""
Overlay Flutuante - Neural Binary Signals
Janela transparente que fica sobre a corretora
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *

class SignalOverlay(QWidget):
    """Janela flutuante transparente que mostra sinais em tempo real"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 350, 450)
        
        # Configurar estilo
        self.setStyleSheet("""
            QWidget#main_frame {
                background-color: rgba(20, 20, 40, 220);
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
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QPushButton#buy {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton#buy:hover {
                background-color: #94e2d5;
            }
            QPushButton#sell {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton#sell:hover {
                background-color: #eba0ac;
            }
        """)
        
        self.init_ui()
        self.current_signal = None
        self.start_drag_pos = None
        
    def init_ui(self):
        """Cria a interface do overlay"""
        # Widget principal
        main = QWidget()
        main.setObjectName("main_frame")
        layout = QVBoxLayout(main)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ===== BARRA DE TÍTULO =====
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("📊 NEURAL SIGNALS")
        title.setStyleSheet("font-weight: bold; color: #cba6f7; font-size: 16px;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # Botão minimizar
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
        
        # Botão fechar
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
        
        # ===== INFORMAÇÕES DO SINAL =====
        self.signal_frame = QWidget()
        signal_layout = QVBoxLayout(self.signal_frame)
        signal_layout.setSpacing(5)
        
        # Símbolo e hora
        header = QHBoxLayout()
        self.symbol_label = QLabel("USD/JPY")
        self.symbol_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(self.symbol_label)
        
        header.addStretch()
        
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        header.addWidget(self.time_label)
        signal_layout.addLayout(header)
        
        # Preço
        self.price_label = QLabel("--")
        self.price_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #cdd6f4;")
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_layout.addWidget(self.price_label)
        
        # Sinal (CALL/PUT)
        self.signal_label = QLabel("AGUARDANDO...")
        self.signal_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #cba6f7;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        """)
        self.signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_layout.addWidget(self.signal_label)
        
        # Confiança
        self.confidence_label = QLabel("0% PROBABILIDADE")
        self.confidence_label.setStyleSheet("font-size: 18px; color: #a6e3a1;")
        self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_layout.addWidget(self.confidence_label)
        
        layout.addWidget(self.signal_frame)
        
        # ===== BOTÃO ENTRAR =====
        self.entry_btn = QPushButton("🚀 ENTRAR AGORA")
        self.entry_btn.setFixedHeight(45)
        self.entry_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #89b4fa, stop:1 #cba6f7);
                color: white;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #74c7ec, stop:1 #cba6f7);
            }
        """)
        self.entry_btn.clicked.connect(self.on_entry_clicked)
        layout.addWidget(self.entry_btn)
        
        # ===== ÚLTIMO SINAL =====
        last_frame = QWidget()
        last_layout = QHBoxLayout(last_frame)
        last_layout.setContentsMargins(0, 5, 0, 5)
        
        last_label = QLabel("Último sinal:")
        last_label.setStyleSheet("color: #a6adc8;")
        last_layout.addWidget(last_label)
        
        self.last_signal_label = QLabel("--")
        self.last_signal_label.setStyleSheet("font-weight: bold;")
        last_layout.addWidget(self.last_signal_label)
        
        last_layout.addStretch()
        
        self.last_time_label = QLabel("--")
        self.last_time_label.setStyleSheet("color: #a6adc8;")
        last_layout.addWidget(self.last_time_label)
        
        layout.addWidget(last_frame)
        
        self.setCentralWidget(main)
        
    def mousePressEvent(self, event):
        """Inicia arraste da janela"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        """Move a janela"""
        if self.start_drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.start_drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.start_drag_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        """Finaliza arraste"""
        self.start_drag_pos = None
    
    def update_signal(self, data):
        """Atualiza o overlay com um novo sinal"""
        self.current_signal = data
        
        # Símbolo
        self.symbol_label.setText(data.get('symbol', '--'))
        
        # Hora
        self.time_label.setText(data.get('timestamp', '--:--:--'))
        
        # Preço (simulado)
        price = data.get('price', '--')
        self.price_label.setText(str(price))
        
        # Sinal
        signal_type = data.get('type', 'NEUTRAL')
        if signal_type == 'CALL':
            self.signal_label.setText("📈 COMPRA")
            self.signal_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #a6e3a1;
                padding: 10px; background: rgba(166, 227, 161, 0.1);
                border-radius: 10px;
            """)
            self.entry_btn.setText("📈 COMPRAR")
            self.entry_btn.setObjectName("buy")
        elif signal_type == 'PUT':
            self.signal_label.setText("📉 VENDA")
            self.signal_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #f38ba8;
                padding: 10px; background: rgba(243, 139, 168, 0.1);
                border-radius: 10px;
            """)
            self.entry_btn.setText("📉 VENDER")
            self.entry_btn.setObjectName("sell")
        else:
            self.signal_label.setText("⏸ NEUTRO")
            self.signal_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #a6adc8;
                padding: 10px; background: rgba(255,255,255,0.05);
                border-radius: 10px;
            """)
            self.entry_btn.setText("⏸ AGUARDAR")
        
        # Confiança
        confidence = data.get('confidence', 0) * 100
        self.confidence_label.setText(f"{confidence:.1f}% PROBABILIDADE")
        
        # Último sinal
        self.last_signal_label.setText(signal_type)
        if signal_type == 'CALL':
            self.last_signal_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        elif signal_type == 'PUT':
            self.last_signal_label.setStyleSheet("color: #f38ba8; font-weight: bold;")
        else:
            self.last_signal_label.setStyleSheet("color: #a6adc8;")
        self.last_time_label.setText(data.get('timestamp', '--'))
        
        # Mostrar janela
        self.show()
        self.raise_()
        self.activateWindow()
    
    def on_entry_clicked(self):
        """Botão ENTRAR AGORA foi clicado"""
        if self.current_signal:
            signal_type = self.current_signal.get('type', 'NEUTRAL')
            symbol = self.current_signal.get('symbol', '--')
            confidence = self.current_signal.get('confidence', 0)
            
            msg = f"""
📊 **SINAL CONFIRMADO**

Ativo: {symbol}
Sinal: {signal_type}
Confiança: {confidence:.1%}

Deseja realmente entrar?
            """
            reply = QMessageBox.question(
                self,
                "Confirmar Entrada",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(
                    self,
                    "✅ Entrada Confirmada",
                    f"Entrada {signal_type} em {symbol} registrada!"
                )
                self.current_signal['status'] = 'EXECUTADO'
                print(f"ENTRADA: {signal_type} {symbol} com {confidence:.1%} confiança")


class OverlayManager:
    """Gerencia o overlay e conexão com o motor de sinais"""
    
    def __init__(self, engine):
        self.engine = engine
        self.overlay = SignalOverlay()
        self.running = True
        
    def start(self):
        """Inicia o overlay"""
        self.overlay.show()
        
        # Thread para atualizar sinais
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_signal)
        self.timer.start(3000)  # A cada 3 segundos
        
    def check_signal(self):
        """Verifica e atualiza o sinal"""
        try:
            import pandas as pd
            import numpy as np
            
            # Gera dados sintéticos
            np.random.seed(int(QTime.currentTime().msec()))
            prices = 100 + np.cumsum(np.random.randn(100) * 0.3)
            data = pd.DataFrame({
                'open': prices[:-1],
                'high': prices[:-1] + np.abs(np.random.randn(99) * 0.2),
                'low': prices[:-1] - np.abs(np.random.randn(99) * 0.2),
                'close': prices[1:],
                'volume': np.random.randint(1000, 5000, 99)
            })
            
            symbol = "USD/JPY"
            signal = self.engine.analyze(data, symbol, "M5")
            
            if signal:
                # Preço simulado
                price = round(prices[-1], 3)
                
                data = {
                    'symbol': symbol,
                    'type': signal.signal_type.value,
                    'confidence': signal.confidence,
                    'strength': signal.strength.value,
                    'price': price,
                    'timestamp': QTime.currentTime().toString('HH:mm:ss'),
                    'reasons': signal.reasons[:3]
                }
                
                self.overlay.update_signal(data)
                
        except Exception as e:
            print(f"Erro no overlay: {e}")


def run_overlay():
    """Inicia o overlay flutuante"""
    from ..core import DecisionEngine
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    engine = DecisionEngine()
    manager = OverlayManager(engine)
    manager.start()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()