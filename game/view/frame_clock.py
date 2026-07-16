from __future__ import annotations

import time
from typing import Callable


class FrameClock:
    """Measures real (wall-clock) time for the live render loop - never
    used by tests of game logic, which use RealTimeArbiter.advance_time(ms)
    with explicit values instead. time_source is injectable so this
    class's own tests don't need a real sleep either."""

    def __init__(self, time_source: Callable[[], float] = time.perf_counter) -> None:
        self._time_source = time_source
        self._last_tick = time_source()

    def tick_ms(self) -> int:
        """Milliseconds elapsed since the previous tick_ms() call (or
        since construction, for the first call) - feeds both
        GameEngine.wait() and PieceAnimatorRegistry.advance_time() with
        the same value, so visual and engine timing never drift apart."""
        now = self._time_source()
        elapsed = now - self._last_tick
        self._last_tick = now
        return int(elapsed * 1000)
