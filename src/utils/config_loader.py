"""Carregador de Configuracoes"""
import json
import os
from typing import Dict

class ConfigLoader:
    """Carrega e gerencia configuracoes do sistema."""

    _config_cache = None

    @classmethod
    def load(cls, path: str = "config/settings.json") -> Dict:
        if cls._config_cache is not None:
            return cls._config_cache

        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo de configuracao nao encontrado: {path}")

        with open(path, "r") as f:
            cls._config_cache = json.load(f)

        env_path = os.path.join(os.path.dirname(path), ".env")
        if os.path.exists(env_path):
            cls._load_env(env_path)

        return cls._config_cache

    @classmethod
    def _load_env(cls, env_path: str):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

    @classmethod
    def reload(cls):
        cls._config_cache = None
