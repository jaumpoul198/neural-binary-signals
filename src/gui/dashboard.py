"""Dashboard Visual em PyQt6"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QProgressBar, QGroupBox, QGridLayout, QTextEdit, QSplitter
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from datetime import datetime

from ..core.engine import SignalEngine
from ..signals.manager import SignalManager
from ..signals.notifier import SignalNotifier


class SignalWorker(QThread):
    signal_ready = pyqtSignal(dict)
    stats_update = pyqtSignal(dict)

    def __init__(self, engine: SignalEngine, pairs: list, timeframe: str):
        super().__init__()
        self.engine = engine
        self.pairs = pairs
        self.timeframe = timeframe
        self.running = True

    def run(self):
        while self.running:
            for pair in self.pairs:
                if not self.running:
                    break
                signal = self.engine.analyze_pair(pair, self.timeframe)
                if signal:
                    self.signal_ready.emit(signal)

            stats = self.engine.get_stats()
            self.stats_update.emit(stats)
            self.msleep(5000)

    def stop(self):
        self.running = False


class SignalDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neural Binary Signals v2.0")
        self.setGeometry(100, 100, 1400, 900)

        self.engine = SignalEngine()
        self.manager = SignalManager()
        self.notifier = SignalNotifier()

        self.worker = None
        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        header = self._create_header()
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 900])
        layout.addWidget(splitter)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)

    def _create_header(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        title = QLabel("NEURAL BINARY SIGNALS")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #00f5ff;")
        layout.addWidget(title)

        self.status_label = QLabel("OFFLINE")
        self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.pair_combo = QComboBox()
        self.pair_combo.addItems([
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
            "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC"
        ])
        layout.addWidget(QLabel("Par:"))
        layout.addWidget(self.pair_combo)

        self.tf_combo = QComboBox()
        self.tf_combo.addItems(["M1", "M5", "M15"])
        self.tf_combo.setCurrentText("M5")
        layout.addWidget(QLabel("TF:"))
        layout.addWidget(self.tf_combo)

        self.start_btn = QPushButton("INICIAR")
        self.start_btn.setStyleSheet("background-color: #00ff88; color: #0f0f1a; font-weight: bold; padding: 10px 20px; border-radius: 8px;")
        self.start_btn.clicked.connect(self.start_analysis)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("PARAR")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_analysis)
        layout.addWidget(self.stop_btn)

        return widget

    def _create_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        signal_group = QGroupBox("SINAL ATIVO")
        signal_layout = QVBoxLayout(signal_group)

        self.signal_direction = QLabel("AGUARDANDO...")
        self.signal_direction.setFont(QFont("Inter", 36, QFont.Weight.Bold))
        self.signal_direction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signal_direction.setStyleSheet("color: #8892b0;")
        signal_layout.addWidget(self.signal_direction)

        self.signal_pair = QLabel("-")
        self.signal_pair.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signal_pair.setFont(QFont("Inter", 14))
        signal_layout.addWidget(self.signal_pair)

        self.signal_confidence = QProgressBar()
        self.signal_confidence.setRange(0, 100)
        self.signal_confidence.setValue(0)
        self.signal_confidence.setTextVisible(True)
        signal_layout.addWidget(self.signal_confidence)

        self.signal_reasons = QTextEdit()
        self.signal_reasons.setReadOnly(True)
        self.signal_reasons.setMaximumHeight(150)
        signal_layout.addWidget(self.signal_reasons)

        layout.addWidget(signal_group)

        stats_group = QGroupBox("ESTATISTICAS")
        stats_layout = QGridLayout(stats_group)

        self.stats_labels = {}
        stats_data = [
            ("Win Rate:", "0%"),
            ("Sinais Hoje:", "0"),
            ("Memoria Ativa:", "0"),
            ("Pares Monitorados:", "0"),
        ]

        for i, (label, value) in enumerate(stats_data):
            stats_layout.addWidget(QLabel(label), i, 0)
            self.stats_labels[label] = QLabel(value)
            self.stats_labels[label].setStyleSheet("color: #00f5ff; font-weight: bold;")
            stats_layout.addWidget(self.stats_labels[label], i, 1)

        layout.addWidget(stats_group)

        history_group = QGroupBox("HISTORICO")
        history_layout = QVBoxLayout(history_group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Hora", "Par", "Direcao", "Conf.", "Resultado", "Padrao"
        ])
        self.history_table.setMaximumHeight(300)
        history_layout.addWidget(self.history_table)

        layout.addWidget(history_group)

        return widget

    def _create_right_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.price_plot = pg.PlotWidget()
        self.price_plot.setTitle("Preco em Tempo Real")
        self.price_plot.setLabel('left', 'Preco')
        self.price_plot.setLabel('bottom', 'Tempo')
        self.price_plot.showGrid(x=True, y=True)
        self.price_curve = self.price_plot.plot(pen=pg.mkPen('#00f5ff', width=2))
        layout.addWidget(self.price_plot)

        self.indicator_plot = pg.PlotWidget()
        self.indicator_plot.setTitle("Indicadores")
        self.indicator_plot.setMaximumHeight(200)
        layout.addWidget(self.indicator_plot)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        return widget

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0f0f1a; }
            QWidget { background-color: #0f0f1a; color: #e0e0e0; }
            QGroupBox { border: 1px solid #333; border-radius: 8px; margin-top: 10px; font-weight: bold; color: #00f5ff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QComboBox, QPushButton { background-color: #1a1a2e; border: 1px solid #333; padding: 5px; border-radius: 4px; }
            QTableWidget { background-color: #1a1a2e; border: 1px solid #333; gridline-color: #333; }
            QHeaderView::section { background-color: #16213e; padding: 5px; border: 1px solid #333; }
            QTextEdit { background-color: #1a1a2e; border: 1px solid #333; color: #e0e0e0; }
        """)

    def start_analysis(self):
        pairs = [self.pair_combo.currentText()]
        tf = self.tf_combo.currentText()

        self.worker = SignalWorker(self.engine, pairs, tf)
        self.worker.signal_ready.connect(self.on_signal)
        self.worker.stats_update.connect(self.on_stats_update)
        self.worker.start()

        self.status_label.setText("ONLINE")
        self.status_label.setStyleSheet("color: #00ff88; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log("Analise iniciada")

    def stop_analysis(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()

        self.status_label.setText("OFFLINE")
        self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("Analise parada")

    def on_signal(self, signal: dict):
        direction = signal["direction"]
        confidence = signal["confidence"]

        self.signal_direction.setText(direction)
        color = "#00ff88" if direction == "CALL" else "#ff4444"
        self.signal_direction.setStyleSheet(f"color: {color};")

        self.signal_pair.setText(f"{signal['pair']} | {signal['timeframe']}")
        self.signal_confidence.setValue(int(confidence))

        reasons = "\n".join(f"- {r}" for r in signal["reasons"])
        self.signal_reasons.setText(reasons)

        self.add_to_history(signal)
        self.notifier.notify_signal(signal)
        self.manager.add_signal(signal)
        self.log(f"SINAL: {direction} {signal['pair']} @ {confidence}%")

    def on_stats_update(self, stats: dict):
        self.stats_labels["Sinais Hoje:"].setText(str(stats.get("daily_signals", 0)))
        self.stats_labels["Memoria Ativa:"].setText(str(stats.get("total_patterns_memory", 0)))

    def add_to_history(self, signal: dict):
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)

        self.history_table.setItem(row, 0, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        self.history_table.setItem(row, 1, QTableWidgetItem(signal["pair"]))

        dir_item = QTableWidgetItem(signal["direction"])
        dir_item.setForeground(QColor("#00ff88" if signal["direction"] == "CALL" else "#ff4444"))
        self.history_table.setItem(row, 2, dir_item)

        self.history_table.setItem(row, 3, QTableWidgetItem(f"{signal['confidence']}%"))
        self.history_table.setItem(row, 4, QTableWidgetItem("PENDENTE"))
        self.history_table.setItem(row, 5, QTableWidgetItem(
            signal.get("snapshot", {}).get("candlestick_patterns", ["-"])[0]
        ))

    def update_ui(self):
        pass

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        self.stop_analysis()
        event.accept()


def launch_dashboard():
    app = QApplication(sys.argv)
    dashboard = SignalDashboard()
    dashboard.show()
    sys.exit(app.exec())
