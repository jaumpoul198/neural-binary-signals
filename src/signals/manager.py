"""Signal Manager"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class SignalManager:
    """Gerenciador de sinais."""

    def __init__(self, history_file: str = "data/history/signals.json"):
        self.history_file = history_file
        self.signals: List[Dict] = []
        self.pending_signals: List[Dict] = []
        self._load_history()

    def add_signal(self, signal: Dict):
        signal["id"] = f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal['pair']}"
        signal["status"] = "PENDING"
        signal["result"] = None
        signal["exit_price"] = None
        signal["profit"] = None

        self.signals.append(signal)
        self.pending_signals.append(signal)
        self._save_history()
        return signal["id"]

    def update_signal_result(self, signal_id: str, result: str, exit_price: Optional[float] = None):
        for signal in self.signals:
            if signal["id"] == signal_id:
                signal["status"] = "CLOSED"
                signal["result"] = result
                signal["exit_price"] = exit_price
                signal["closed_at"] = datetime.now().isoformat()
                self.pending_signals = [s for s in self.pending_signals if s["id"] != signal_id]
                self._save_history()
                return True
        return False

    def get_today_signals(self) -> List[Dict]:
        today = datetime.now().date()
        return [s for s in self.signals if datetime.fromisoformat(s["timestamp"]).date() == today]

    def get_stats(self, period: str = "today") -> Dict:
        now = datetime.now()
        if period == "today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            cutoff = now - timedelta(days=7)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = datetime.min

        filtered = [s for s in self.signals if datetime.fromisoformat(s["timestamp"]) >= cutoff]
        closed = [s for s in filtered if s["status"] == "CLOSED"]
        wins = [s for s in closed if s["result"] == "WIN"]
        losses = [s for s in closed if s["result"] == "LOSS"]

        total = len(closed)
        win_rate = (len(wins) / total * 100) if total > 0 else 0

        pair_stats = {}
        for s in closed:
            pair = s["pair"]
            if pair not in pair_stats:
                pair_stats[pair] = {"wins": 0, "losses": 0, "total": 0}
            pair_stats[pair]["total"] += 1
            if s["result"] == "WIN":
                pair_stats[pair]["wins"] += 1
            else:
                pair_stats[pair]["losses"] += 1

        call_signals = [s for s in closed if s["direction"] == "CALL"]
        put_signals = [s for s in closed if s["direction"] == "PUT"]
        call_wins = len([s for s in call_signals if s["result"] == "WIN"])
        put_wins = len([s for s in put_signals if s["result"] == "WIN"])

        return {
            "period": period,
            "total_signals": len(filtered),
            "closed_signals": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 2),
            "pending": len(self.pending_signals),
            "call_win_rate": round(call_wins / len(call_signals) * 100, 2) if call_signals else 0,
            "put_win_rate": round(put_wins / len(put_signals) * 100, 2) if put_signals else 0,
            "pair_stats": pair_stats,
            "avg_confidence": round(sum(s["confidence"] for s in closed) / len(closed), 2) if closed else 0,
            "best_pair": max(pair_stats.items(), key=lambda x: x[1]["wins"])[0] if pair_stats else None,
        }

    def export_report(self, filename: str = None) -> str:
        if filename is None:
            filename = f"data/history/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "stats": self.get_stats("all"),
            "signals": self.signals,
        }

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        return filename

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r") as f:
                self.signals = json.load(f)
            self.pending_signals = [s for s in self.signals if s["status"] == "PENDING"]
        except Exception as e:
            print(f"Erro ao carregar historico: {e}")

    def _save_history(self):
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(self.signals, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar historico: {e}")
