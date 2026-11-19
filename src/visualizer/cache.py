"""Byte ledger + LRU caches for the visualizer UI process (WI-085).

The UI holds one worker's worth of columns. Every projected load is costed as
`rows x cols x 4` BEFORE it happens; requests that would exceed the 3.0 GB resident
budget are refused (`DataBudgetError`) instead of swapping (no-swap VPS).
"""
from __future__ import annotations

import os
from collections import OrderedDict
from typing import Any, Iterable

from src.visualizer import COLUMN_LRU_SIZE, DEFAULT_BUDGET_BYTES, OHLCV_LRU_SIZE

BYTES_PER_FLOAT32 = 4


class DataBudgetError(RuntimeError):
    """A projected load would exceed the resident-column budget."""


class ByteLedger:
    """Tracks the estimated resident bytes of the columns currently held."""

    def __init__(self, budget_bytes: int = DEFAULT_BUDGET_BYTES) -> None:
        self.budget_bytes = int(budget_bytes)
        self._entries: dict[Any, int] = {}

    @staticmethod
    def estimate(rows: int, columns: int | Iterable[str], bytes_per_value: int = BYTES_PER_FLOAT32) -> int:
        n_cols = columns if isinstance(columns, int) else len(list(columns))
        return int(rows) * int(n_cols) * int(bytes_per_value)

    @property
    def used_bytes(self) -> int:
        return sum(self._entries.values())

    @property
    def remaining_bytes(self) -> int:
        return self.budget_bytes - self.used_bytes

    def would_fit(self, nbytes: int) -> bool:
        return self.used_bytes + int(nbytes) <= self.budget_bytes

    def reserve(self, key: Any, nbytes: int, label: str = "") -> None:
        """Reserve `nbytes` under `key`, or raise `DataBudgetError` without mutating state."""
        nbytes = int(nbytes)
        if not self.would_fit(nbytes):
            raise DataBudgetError(
                f"refused load {label or key}: needs {nbytes / 2**20:.1f} MB, "
                f"{self.remaining_bytes / 2**20:.1f} MB of {self.budget_bytes / 2**20:.0f} MB left"
            )
        self.release(key)
        self._entries[key] = nbytes

    def release(self, key: Any) -> int:
        return int(self._entries.pop(key, 0))

    def snapshot(self) -> dict:
        return {
            "budget_bytes": self.budget_bytes,
            "used_bytes": self.used_bytes,
            "remaining_bytes": self.remaining_bytes,
            "n_entries": len(self._entries),
        }


class LRUCache:
    """Minimal LRU. `put` returns the evicted keys so the caller can free ledger bytes."""

    def __init__(self, capacity: int, name: str = "lru") -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = int(capacity)
        self.name = name
        self._items: OrderedDict[Any, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Any | None:
        if key in self._items:
            self._items.move_to_end(key)
            self.hits += 1
            return self._items[key]
        self.misses += 1
        return None

    def put(self, key: Any, value: Any) -> list[Any]:
        evicted: list[Any] = []
        if key in self._items:
            self._items.move_to_end(key)
        self._items[key] = value
        while len(self._items) > self.capacity:
            old_key, _ = self._items.popitem(last=False)
            evicted.append(old_key)
        return evicted

    def __contains__(self, key: Any) -> bool:
        return key in self._items

    def __len__(self) -> int:
        return len(self._items)

    def keys(self) -> list[Any]:
        return list(self._items)

    def clear(self) -> list[Any]:
        old = list(self._items)
        self._items.clear()
        return old

    def stats(self) -> dict:
        return {"name": self.name, "capacity": self.capacity, "size": len(self._items), "hits": self.hits, "misses": self.misses}


def make_caches() -> tuple[LRUCache, LRUCache]:
    """Column cache (keyed by source/market/columns) and the 32-symbol OHLCV cache."""
    return LRUCache(COLUMN_LRU_SIZE, "columns"), LRUCache(OHLCV_LRU_SIZE, "ohlcv")


def process_rss_bytes() -> int:
    """Resident set size of this process (psutil, with a /proc fallback)."""
    try:
        import psutil

        return int(psutil.Process(os.getpid()).memory_info().rss)
    except Exception:  # pragma: no cover - psutil is a declared dependency
        with open("/proc/self/statm", "r", encoding="ascii") as handle:
            pages = int(handle.read().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE")
