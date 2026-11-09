"""WI-032 — swing-anchored 3-class buy/sell/hold (D-021)."""
from src.swing_bsh.events import (
    BARRIERS,
    BUY,
    CLUSTER_GAP,
    HOLD,
    K_VALUES,
    SELL,
    STATES,
    SWING_WINDOW,
    detect_swings,
    first_touch_label,
    label_symbol,
    sample_events,
)

__all__ = [
    "BARRIERS", "BUY", "CLUSTER_GAP", "HOLD", "K_VALUES", "SELL", "STATES",
    "SWING_WINDOW", "detect_swings", "first_touch_label", "label_symbol", "sample_events",
]
