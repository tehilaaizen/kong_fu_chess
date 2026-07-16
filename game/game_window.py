from __future__ import annotations

from typing import Protocol

import cv2

from engine.game_snapshot import GameSnapshot
from input.controller import Controller
from view.frame_clock import FrameClock
from view.piece_animator_registry import PieceAnimatorRegistry
from view.renderer import Renderer

DEFAULT_WINDOW_NAME = "Kong Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 27 == Esc
FRAME_DELAY_MS = 16  # ~60fps, also pumps the window's event queue


class WaitsAndSnapshots(Protocol):
    """The only capability GameWindow needs from a game engine - lets
    tests inject a lightweight fake instead of the real GameEngine."""

    def wait(self, ms: int) -> None:
        ...


class GameWindow:
    """Owns the live interactive window: opens it, forwards mouse clicks
    to Controller, and redraws every frame from whatever GameEngine last
    pushed via on_snapshot (see kung_fu_chess_design_guide.md §12 - this
    class, not view/, is where Controller/GameEngine dependencies belong,
    since view/ must stay pure)."""

    def __init__(
        self,
        renderer: Renderer,
        controller: Controller,
        game_engine: WaitsAndSnapshots,
        clock: FrameClock,
        registry: PieceAnimatorRegistry,
        window_name: str = DEFAULT_WINDOW_NAME,
    ) -> None:
        self._renderer = renderer
        self._controller = controller
        self._game_engine = game_engine
        self._clock = clock
        self._registry = registry
        self._window_name = window_name
        self._latest_snapshot: GameSnapshot | None = None

    def on_snapshot(self, snapshot: GameSnapshot) -> None:
        """GameObserver hook: just remember the latest snapshot - drawing
        happens in run()'s own loop, not here, so this stays trivially
        testable without a real window."""
        self._latest_snapshot = snapshot

    def _on_mouse_event(self, event: int, x: int, y: int, flags: int, userdata: object) -> None:
        """Forward a left-button click to Controller; ignore everything
        else. No board-mapping/selection logic of its own - that's
        already Controller's job."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.click(x, y)

    def run(self) -> None:
        """Open the window and loop until the user quits: advance
        simulated time by however much real time passed, then redraw the
        latest snapshot's current animation frames. Not unit-tested (a
        real, blocking GUI loop) - same category as Img.show()/show_frame()."""
        cv2.namedWindow(self._window_name)
        cv2.setMouseCallback(self._window_name, self._on_mouse_event)
        self._game_engine.wait(0)

        while True:
            elapsed_ms = self._clock.tick_ms()
            self._game_engine.wait(elapsed_ms)

            if self._latest_snapshot is not None:
                now_ms = self._clock.now_ms()
                self._registry.update(self._latest_snapshot, now_ms)
                frames = self._registry.current_frames(self._latest_snapshot, now_ms)
                self._renderer.render_snapshot(self._latest_snapshot, frames).show_frame(self._window_name)

            if cv2.waitKey(FRAME_DELAY_MS) & 0xFF in QUIT_KEYS:
                break

        cv2.destroyAllWindows()
