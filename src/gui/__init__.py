"""
GUI Module - Interface gráfica
"""

from .dashboard import Dashboard, run_dashboard
from .overlay import SignalOverlay, run_overlay

__all__ = ['Dashboard', 'run_dashboard', 'SignalOverlay', 'run_overlay']