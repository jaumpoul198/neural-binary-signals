"""
Memória Neural Fotográfica
Sistema que armazena snapshots de mercado e encontra padrões similares.

Funcionamento:
1. Cada snapshot é convertido em um vetor de features
2. Padrões são armazenados com resultado (WIN/LOSS)
3. Busca por similaridade usando distância euclidiana/cosseno
4. Predição baseada nos resultados dos padrões mais similares
"""

import numpy as np
import json
import pickle
import os
from typing import List, Tuple, Optional
from datetime import datetime
from collections import deque

from ..core.snapshot import MarketSnapshot


class NeuralMemory:
    """
    Memória fotográfica neural para reconhecimento de padrões de mercado.

    Armazena snapshots vetorizados e permite busca por similaridade
    para prever resultados baseados em padrões históricos.
    """

    def __init__(self, similarity_threshold: float = 0.85, 
                 max_patterns: int = 50000,
                 memory_file: str = "data/patterns/neural_memory.pkl"):
        self.similarity_threshold = similarity_threshold
        self.max_patterns = max_patterns
        self.memory_file = memory_file

        self.patterns: List[MarketSnapshot] = []
        self.vectors: List[np.ndarray] = []
        self.results: List[str] = []  # "WIN" ou "LOSS"

        self._load_memory()

    def store(self, snapshot: MarketSnapshot):
        """
        Armazena um snapshot na memória neural.

        Se o snapshot já tem resultado, armazena permanentemente.
        Se não tem resultado, armazena temporariamente para atualização posterior.
        """
        vector = snapshot.to_feature_vector()

        # Verificar se já existe padrão muito similar (evitar duplicatas)
        if len(self.vectors) > 0:
            similarities = self._calculate_similarities(vector)
            if np.max(similarities) > 0.98:
                return  # Padrão muito similar já existe

        self.patterns.append(snapshot)
        self.vectors.append(vector)
        self.results.append(snapshot.result if snapshot.result else "PENDING")

        # Limitar tamanho da memória (FIFO com prioridade para WINs)
        if len(self.patterns) > self.max_patterns:
            self._prune_memory()

        self._save_memory()

    def find_similar(self, snapshot: MarketSnapshot, 
                     top_k: int = 5) -> List[Tuple[MarketSnapshot, float]]:
        """
        Encontra os padrões mais similares ao snapshot atual.

        Args:
            snapshot: Snapshot atual para comparar
            top_k: Número de padrões similares a retornar

        Returns:
            Lista de tuplas (padrão, similaridade)
        """
        if len(self.vectors) < self.config_min_history():
            return []

        query_vector = snapshot.to_feature_vector()
        similarities = self._calculate_similarities(query_vector)

        # Filtrar por threshold e resultados conhecidos
        valid_indices = []
        for i, sim in enumerate(similarities):
            if sim >= self.similarity_threshold and self.results[i] in ["WIN", "LOSS"]:
                valid_indices.append((i, sim))

        # Ordenar por similaridade
        valid_indices.sort(key=lambda x: x[1], reverse=True)

        # Retornar top_k
        results = []
        for idx, sim in valid_indices[:top_k]:
            results.append((self.patterns[idx], sim))

        return results

    def predict(self, snapshot: MarketSnapshot) -> Tuple[str, float]:
        """
        Prediz a direção mais provável baseada em padrões similares.

        Returns:
            Tupla (direção_prevista, confiança)
        """
        similar = self.find_similar(snapshot, top_k=10)

        if not similar:
            return "NEUTRAL", 0.0

        call_wins = 0
        put_wins = 0
        total_weight = 0

        for pattern, similarity in similar:
            weight = similarity
            total_weight += weight

            if pattern.result == "WIN":
                if pattern.signal_generated == "CALL":
                    call_wins += weight
                elif pattern.signal_generated == "PUT":
                    put_wins += weight

        if total_weight == 0:
            return "NEUTRAL", 0.0

        call_prob = call_wins / total_weight
        put_prob = put_wins / total_weight

        if call_prob > put_prob:
            return "CALL", call_prob
        elif put_prob > call_prob:
            return "PUT", put_prob

        return "NEUTRAL", 0.0

    def update_result(self, snapshot_timestamp: datetime, result: str):
        """
        Atualiza o resultado de um snapshot pendente.

        Args:
            snapshot_timestamp: Timestamp do snapshot
            result: "WIN" ou "LOSS"
        """
        for i, pattern in enumerate(self.patterns):
            if pattern.timestamp == snapshot_timestamp:
                pattern.result = result
                self.results[i] = result
                self._save_memory()
                return True
        return False

    def get_stats(self) -> dict:
        """Retorna estatísticas da memória neural."""
        wins = self.results.count("WIN")
        losses = self.results.count("LOSS")
        pending = self.results.count("PENDING")
        total = len(self.results)

        win_rate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0

        # Estatísticas por direção
        call_wins = sum(1 for i, p in enumerate(self.patterns) 
                       if p.result == "WIN" and p.signal_generated == "CALL")
        call_losses = sum(1 for i, p in enumerate(self.patterns) 
                         if p.result == "LOSS" and p.signal_generated == "CALL")
        put_wins = sum(1 for i, p in enumerate(self.patterns) 
                      if p.result == "WIN" and p.signal_generated == "PUT")
        put_losses = sum(1 for i, p in enumerate(self.patterns) 
                        if p.result == "LOSS" and p.signal_generated == "PUT")

        return {
            "total_patterns": total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": round(win_rate, 2),
            "call_win_rate": round(call_wins / (call_wins + call_losses) * 100, 2) if (call_wins + call_losses) > 0 else 0,
            "put_win_rate": round(put_wins / (put_wins + put_losses) * 100, 2) if (put_wins + put_losses) > 0 else 0,
            "memory_usage_percent": round(len(self.patterns) / self.max_patterns * 100, 2),
        }

    def _calculate_similarities(self, query_vector: np.ndarray) -> np.ndarray:
        """
        Calcula similaridade cosseno entre query e todos os vetores armazenados.
        """
        if len(self.vectors) == 0:
            return np.array([])

        vectors_array = np.array(self.vectors)

        # Similaridade cosseno
        dot_product = np.dot(vectors_array, query_vector)
        query_norm = np.linalg.norm(query_vector)
        vectors_norm = np.linalg.norm(vectors_array, axis=1)

        cosine_sim = dot_product / (vectors_norm * query_norm + 1e-8)

        # Converter para escala 0-1 (cosseno vai de -1 a 1)
        similarity = (cosine_sim + 1) / 2

        return similarity

    def _prune_memory(self):
        """
        Podar memória quando atinge o limite.
        Mantém padrões WIN e remove os mais antigos LOSS.
        """
        # Separar por resultado
        win_indices = [i for i, r in enumerate(self.results) if r == "WIN"]
        loss_indices = [i for i, r in enumerate(self.results) if r == "LOSS"]
        pending_indices = [i for i, r in enumerate(self.results) if r == "PENDING"]

        # Manter todos os WINs, metade dos LOSSs, todos os PENDINGs recentes
        keep_loss = loss_indices[-len(loss_indices)//2:] if len(loss_indices) > 100 else loss_indices
        keep_pending = pending_indices[-50:] if len(pending_indices) > 50 else pending_indices

        keep_indices = sorted(win_indices + keep_loss + keep_pending)

        self.patterns = [self.patterns[i] for i in keep_indices]
        self.vectors = [self.vectors[i] for i in keep_indices]
        self.results = [self.results[i] for i in keep_indices]

    def _save_memory(self):
        """Salva memória em disco."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            data = {
                "patterns": [p.to_dict() for p in self.patterns],
                "vectors": [v.tolist() for v in self.vectors],
                "results": self.results,
            }
            with open(self.memory_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Erro ao salvar memória: {e}")

    def _load_memory(self):
        """Carrega memória do disco."""
        if not os.path.exists(self.memory_file):
            return

        try:
            with open(self.memory_file, "rb") as f:
                data = pickle.load(f)

            self.patterns = [MarketSnapshot.from_dict(d) for d in data["patterns"]]
            self.vectors = [np.array(v, dtype=np.float32) for v in data["vectors"]]
            self.results = data["results"]

            print(f"Memória neural carregada: {len(self.patterns)} padrões")
        except Exception as e:
            print(f"Erro ao carregar memória: {e}")

    def config_min_history(self) -> int:
        """Retorna número mínimo de padrões para predição."""
        return 100  # Mínimo para predições confiáveis
