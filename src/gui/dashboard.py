"""
Dashboard Neural Binary Signals
Interface gráfica para monitoramento de sinais
"""

import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ..core import DecisionEngine
import pandas as pd
import numpy as np
import threading
import time

class SignalWorker(QThread):
    """Thread para gerar sinais em background"""
    signal_ready = pyqtSignal(dict)
    
    def __init__(self, engine, symbol, timeframe):
        super().__init__()
        self.engine = engine
        self.symbol = symbol
        self.timeframe = timeframe
        self.running = True
        
    def run(self):
        while self.running:
            try:
                # Gera dados sintéticos
                np.random.seed(int(time.time()))
                prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
                data = pd.DataFrame({
                    'open': prices[:-1],
                    'high': prices[:-1] + np.abs(np.random.randn(99) * 0.3),
                    'low': prices[:-1] - np.abs(np.random.randn(99) * 0.3),
                    'close': prices[1:],
                    'volume': np.random.randint(1000, 5000, 99)
                })
                
                signal = self.engine.analyze(data, self.symbol, self.timeframe)
                if signal:
                    self.signal_ready.emit({
                        'symbol': self.symbol,
                        'type': signal.signal_type.value,
                        'confidence': signal.confidence,
                        'strength': signal.strength.value,
                        'reasons': signal.reasons[:3],
                        'timestamp': signal.timestamp.strftime('%H:%M:%S')
                    })
                time.sleep(5)
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(2)
    
    def stop(self):
        self.running = False


class Dashboard(QMainWindow):
    """Janela principal do dashboard"""
    
    def __init__(self):
        super().__init__()
        self.engine = DecisionEngine()
        self.setWindowTitle("📊 Neural Binary Signals")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet(self.get_styles())
        
        self.symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTC", "ETH"]
        self.timeframes = ["M1", "M5", "M15"]
        self.selected_symbol = "EURUSD"
        self.selected_timeframe = "M5"
        self.workers = {}
        self.signals_history = []
        
        self.init_ui()
        self.start_all()
    
    def get_styles(self):
        return """
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 14px; }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #585b70; }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QTableWidget {
                background-color: #313244;
                color: #cdd6f4;
                gridline-color: #45475a;
                font-size: 13px;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #45475a;
                color: #cdd6f4;
                padding: 8px;
                border: none;
            }
            QGroupBox {
                color: #cdd6f4;
                border: 2px solid #45475a;
                border-radius: 10px;
                margin-top: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 10px; }
            QScrollArea { border: none; background: transparent; }
            QListWidget {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                font-size: 13px;
            }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #585b70; }
        """
    
    def init_ui(self):
        """Configura a interface"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # TOPO: CONTROLES
        top_frame = QFrame()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setSpacing(15)
        
        title = QLabel("📈 NEURAL BINARY SIGNALS")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #cba6f7;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        top_layout.addWidget(QLabel("Ativo:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(self.symbols)
        self.symbol_combo.currentTextChanged.connect(self.change_symbol)
        top_layout.addWidget(self.symbol_combo)
        
        top_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(self.timeframes)
        self.timeframe_combo.currentTextChanged.connect(self.change_timeframe)
        top_layout.addWidget(self.timeframe_combo)
        
        self.start_btn = QPushButton("▶ Iniciar")
        self.start_btn.clicked.connect(self.start_all)
        top_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Parar")
        self.stop_btn.clicked.connect(self.stop_all)
        top_layout.addWidget(self.stop_btn)
        
        layout.addWidget(top_frame)
        
        # CORPO: 3 COLUNAS
        body = QHBoxLayout()
        body.setSpacing(15)
        
        left = self.create_live_signals()
        body.addWidget(left, 1)
        
        center = self.create_signal_detail()
        body.addWidget(center, 1)
        
        right = self.create_history()
        body.addWidget(right, 1)
        
        layout.addLayout(body, 1)
    
    def create_live_signals(self):
        group = QGroupBox("📊 Sinais ao Vivo")
        layout = QVBoxLayout(group)
        
        self.signal_table = QTableWidget()
        self.signal_table.setColumnCount(4)
        self.signal_table.setHorizontalHeaderLabels(["Ativo", "Sinal", "Confiança", "Hora"])
        self.signal_table.horizontalHeader().setStretchLastSection(True)
        self.signal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.signal_table)
        
        self.update_table()
        return group
    
    def create_signal_detail(self):
        group = QGroupBox("📋 Detalhes do Sinal")
        layout = QVBoxLayout(group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                font-size: 14px;
                font-family: 'Courier New';
            }
        """)
        self.detail_text.setText("Aguardando sinal...")
        layout.addWidget(self.detail_text)
        
        return group
    
    def create_history(self):
        group = QGroupBox("📜 Histórico")
        layout = QVBoxLayout(group)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.history_list)
        
        clear_btn = QPushButton("🗑 Limpar Histórico")
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)
        
        return group
    
    def update_table(self):
        self.signal_table.setRowCount(len(self.symbols))
        for i, symbol in enumerate(self.symbols):
            self.signal_table.setItem(i, 0, QTableWidgetItem(symbol))
            self.signal_table.setItem(i, 1, QTableWidgetItem("⏳..."))
            self.signal_table.setItem(i, 2, QTableWidgetItem("0%"))
            self.signal_table.setItem(i, 3, QTableWidgetItem("--:--:--"))
    
    def change_symbol(self, symbol):
        self.selected_symbol = symbol
        self.restart_workers()
    
    def change_timeframe(self, timeframe):
        self.selected_timeframe = timeframe
        self.restart_workers()
    
    def start_all(self):
        self.stop_all()
        for symbol in self.symbols:
            worker = SignalWorker(self.engine, symbol, self.selected_timeframe)
            worker.signal_ready.connect(self.on_signal_received)
            worker.start()
            self.workers[symbol] = worker
    
    def stop_all(self):
        for worker in self.workers.values():
            worker.stop()
        self.workers.clear()
    
    def restart_workers(self):
        self.start_all()
    
    def on_signal_received(self, data):
        symbol = data['symbol']
        signal_type = data['type']
        confidence = data['confidence']
        time_str = data['timestamp']
        
        for i in range(self.signal_table.rowCount()):
            if self.signal_table.item(i, 0).text() == symbol:
                color = "#a6e3a1" if signal_type == "CALL" else "#f38ba8"
                item = QTableWidgetItem(signal_type)
                item.setForeground(QColor(color))
                self.signal_table.setItem(i, 1, item)
                
                conf_item = QTableWidgetItem(f"{confidence:.1%}")
                conf_item.setForeground(QColor("#cba6f7"))
                self.signal_table.setItem(i, 2, conf_item)
                
                self.signal_table.setItem(i, 3, QTableWidgetItem(time_str))
                break
        
        if symbol == self.selected_symbol:
            details = f"""
            🎯 **SINAL DETECTADO**
            
            Ativo: {symbol}
            Sinal: {signal_type}
            Confiança: {confidence:.1%}
            Força: {data['strength']}
            Hora: {time_str}
            
            📊 **ANÁLISE:**
            {chr(10).join('• ' + r for r in data['reasons'])}
            """
            self.detail_text.setText(details)
        
        history_item = f"[{time_str}] {symbol} → {signal_type} ({confidence:.1%})"
        self.history_list.insertItem(0, history_item)
        if self.history_list.count() > 100:
            self.history_list.takeItem(self.history_list.count() - 1)
    
    def clear_history(self):
        self.history_list.clear()


def run_dashboard():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = Dashboard()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_dashboard()