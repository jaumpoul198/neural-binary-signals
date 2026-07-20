"""
Signal Notifier
Sistema de notificações para sinais (som, desktop, Telegram).
"""

import os
import platform
from typing import Optional
from datetime import datetime


class SignalNotifier:
    """
    Notificador de sinais.

    Suporta:
    - Alertas sonoros
    - Notificações desktop
    - Mensagens Telegram (opcional)
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.sound_enabled = self.config.get("sound", True)
        self.desktop_enabled = self.config.get("desktop", True)
        self.telegram_config = self.config.get("telegram", {})

        self._sound_initialized = False
        self._init_sound()

    def _init_sound(self):
        """Inicializa sistema de som."""
        if not self.sound_enabled:
            return

        try:
            import pygame
            pygame.mixer.init()
            self._sound_initialized = True
        except ImportError:
            print("Pygame não instalado. Alertas sonoros desabilitados.")
            self.sound_enabled = False

    def notify_signal(self, signal: dict):
        """
        Envia notificação de novo sinal.

        Args:
            signal: Dicionário com dados do sinal
        """
        direction = signal["direction"]
        pair = signal["pair"]
        confidence = signal["confidence"]

        title = f"SINAL {direction} - {pair}"
        message = (f"Confiança: {confidence}%
"
                  f"Timeframe: {signal['timeframe']}
"
                  f"Preço: {signal['price']:.5f}
"
                  f"Confluência: {signal['confluence']} indicadores")

        if self.sound_enabled:
            self._play_sound(direction)

        if self.desktop_enabled:
            self._desktop_notification(title, message)

        if self.telegram_config.get("enabled"):
            self._telegram_notification(title, message)

    def _play_sound(self, direction: str):
        """Toca som de alerta."""
        if not self._sound_initialized:
            return

        try:
            import pygame
            import numpy as np
            import struct

            # Frequências para CALL (alta) e PUT (baixa)
            if direction == "CALL":
                freq = 880
            else:
                freq = 440

            duration = 0.3
            sample_rate = 44100
            t = [i / sample_rate for i in range(int(duration * sample_rate))]
            wave = [0.5 * np.sin(2 * np.pi * freq * ti) for ti in t]
            audio = b"".join(struct.pack("h", int(sample * 32767)) for sample in wave)

            sound = pygame.mixer.Sound(buffer=audio)
            sound.play()

        except Exception as e:
            print(f"Erro ao tocar som: {e}")

    def _desktop_notification(self, title: str, message: str):
        """Envia notificação desktop."""
        try:
            system = platform.system()

            if system == "Windows":
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10,
                    app_icon=None
                )
            elif system == "Darwin":
                os.system(f'osascript -e 'display notification "{message}" with title "{title}"'')
            else:
                os.system(f'notify-send "{title}" "{message}" --urgency=critical')

        except Exception as e:
            print(f"Erro na notificação desktop: {e}")

    def _telegram_notification(self, title: str, message: str):
        """Envia mensagem via Telegram."""
        try:
            import requests

            bot_token = self.telegram_config.get("bot_token")
            chat_id = self.telegram_config.get("chat_id")

            if not bot_token or not chat_id:
                return

            text = f"*{title}*

{message}"
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }

            requests.post(url, json=payload, timeout=5)

        except Exception as e:
            print(f"Erro no Telegram: {e}")

    def notify_result(self, signal: dict, result: str):
        """
        Notifica resultado de um sinal.

        Args:
            signal: Dicionário com dados do sinal
            result: "WIN" ou "LOSS"
        """
        emoji = "WIN" if result == "WIN" else "LOSS"
        title = f"{emoji} RESULTADO - {signal['pair']}"
        message = f"Direção: {signal['direction']}
Resultado: {result}"

        if self.desktop_enabled:
            self._desktop_notification(title, message)

        if self.telegram_config.get("enabled"):
            self._telegram_notification(title, message)
