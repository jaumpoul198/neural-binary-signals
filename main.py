#!/usr/bin/env python3
"""
Neural Binary Signals - Sistema Principal
Entry point para execucao do sistema.
"""

import argparse
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.engine import SignalEngine
from src.signals.manager import SignalManager
from src.signals.notifier import SignalNotifier
from src.utils.logger import Logger


def run_terminal_mode(args):
    """Executa em modo terminal."""
    logger = Logger()
    engine = SignalEngine()
    manager = SignalManager()
    notifier = SignalNotifier()

    print("=" * 60)
    print("NEURAL BINARY SIGNALS - Modo Terminal")
    print("=" * 60)
    print(f"Par: {args.pair}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Analise continua: {'Sim' if args.continuous else 'Nao'}")
    print("=" * 60)

    if args.continuous:
        print("Analisando... (Ctrl+C para parar)")
        try:
            while True:
                signal = engine.analyze_pair(args.pair, args.timeframe, args.lookback)
                if signal:
                    print("\n" + "!" * 60)
                    print("SINAL DETECTADO!")
                    print(f"Direcao: {signal['direction']}")
                    print(f"Confianca: {signal['confidence']}%")
                    print(f"Confluencia: {signal['confluence']} indicadores")
                    print(f"Preco: {signal['price']:.5f}")
                    print("Razoes:")
                    for reason in signal["reasons"]:
                        print(f"  - {reason}")
                    print("!" * 60 + "\n")

                    notifier.notify_signal(signal)
                    manager.add_signal(signal)
                else:
                    print(".", end="", flush=True)

        except KeyboardInterrupt:
            print("\nAnalise interrompida.")
    else:
        signal = engine.analyze_pair(args.pair, args.timeframe, args.lookback)
        if signal:
            print("\nSINAL ENCONTRADO:")
            print(json.dumps(signal, indent=2, default=str))
        else:
            print("Nenhum sinal encontrado no momento.")

    stats = manager.get_stats("today")
    print("\nEstatisticas de Hoje:")
    print(f"  Sinais: {stats['total_signals']}")
    print(f"  Wins: {stats['wins']}")
    print(f"  Losses: {stats['losses']}")
    print(f"  Win Rate: {stats['win_rate']}%")


def run_analyze_mode(args):
    """Executa analise detalhada."""
    engine = SignalEngine()

    print(f"Analisando {args.pair} no timeframe {args.timeframe}...")
    print(f"Lookback: {args.lookback} candles\n")

    from src.core.market_data import MarketDataEngine
    md = MarketDataEngine()
    df = md.get_historical_data(args.pair, args.timeframe, args.lookback)

    print(f"Dados obtidos: {len(df)} candles")
    print(f"Periodo: {df.index[0]} ate {df.index[-1]}")
    print(f"Preco atual: {df['close'].iloc[-1]:.5f}")
    print(f"Range: {df['low'].min():.5f} - {df['high'].max():.5f}")

    from src.indicators.technical import TechnicalIndicators
    from src.indicators.candlestick import CandlestickPatterns

    ti = TechnicalIndicators()
    cp = CandlestickPatterns()

    config = engine.config["indicators"]
    indicators = ti.calculate_all(df, config)
    patterns = cp.detect_all(df)

    print("\nIndicadores:")
    for key, value in indicators.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    print(f"\nPadroes de Candlestick: {patterns if patterns else 'Nenhum'}")


def main():
    """Funcao principal."""
    parser = argparse.ArgumentParser(
        description="Neural Binary Signals - Sistema de Sinais com Memoria Neural"
    )

    parser.add_argument(
        "--mode", 
        choices=["dashboard", "terminal", "analyze"],
        default="dashboard",
        help="Modo de execucao"
    )
    parser.add_argument("--pair", default="EURUSD", help="Par de moedas")
    parser.add_argument("--timeframe", default="M5", choices=["M1", "M5", "M15"])
    parser.add_argument("--lookback", type=int, default=200, help="Candles para analise")
    parser.add_argument("--continuous", action="store_true", help="Analise continua")

    args = parser.parse_args()

    if args.mode == "dashboard":
        try:
            from src.gui.dashboard import launch_dashboard
            launch_dashboard()
        except ImportError as e:
            print(f"Erro ao carregar GUI: {e}")
            print("Execute: pip install PyQt6 pyqtgraph")
            sys.exit(1)
    elif args.mode == "terminal":
        run_terminal_mode(args)
    elif args.mode == "analyze":
        run_analyze_mode(args)


if __name__ == "__main__":
    main()
