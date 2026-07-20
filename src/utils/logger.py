"""Sistema de Logging"""
import logging
import os
from datetime import datetime

class Logger:
    """Logger configurado para o sistema."""

    def __init__(self, name: str = "neural_binary_signals"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        os.makedirs("logs", exist_ok=True)

        file_handler = logging.FileHandler(
            f"logs/signals_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
