#!/usr/bin/env python
"""
Neural Binary Signals - Entry Point
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Neural Binary Signals")
    parser.add_argument('--mode', choices=['dashboard', 'terminal', 'overlay'], 
                        default='dashboard',
                        help='Modo de execução')
    parser.add_argument('--pair', default='EURUSD',
                        help='Par para monitorar')
    parser.add_argument('--timeframe', default='M5',
                        help='Timeframe (M1, M5, M15)')
    
    args = parser.parse_args()
    
    if args.mode == 'dashboard':
        from src.gui.dashboard import run_dashboard
        run_dashboard()
    elif args.mode == 'overlay':
        from src.gui.overlay import run_overlay
        run_overlay()
    else:
        print(f"Modo terminal para {args.pair} {args.timeframe}")
        print("⚠ Modo terminal em desenvolvimento")

if __name__ == "__main__":
    main()