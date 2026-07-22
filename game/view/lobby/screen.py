from __future__ import annotations

from typing import Protocol

import cv2

from view.image_view import Img
from view.lobby import lobby_theme as theme

FRAME_DELAY_MS = 20
_NO_KEY = 255  # cv2.waitKey returns 0xFF (from -1) when no key was pressed
_ESC_KEY = 27


class Screen(Protocol):
    """One lobby screen. render draws it onto a fresh canvas; on_click and
    on_key feed it mouse and keyboard input; result returns None while the
    screen is still active and a non-None outcome once it is finished (which
    ends its run and is handed back to the caller)."""

    def render(self, canvas: Img) -> None:
        ...

    def on_click(self, x: int, y: int) -> None:
        ...

    def on_key(self, key: int) -> None:
        ...

    def result(self) -> object | None:
        ...


def run_screen(screen: Screen, window_name: str = theme.WINDOW_NAME) -> object | None:
    """Drive one screen in the cv2 window until it produces a result, and
    return that result. Returns None if the user quit (Esc or closed the
    window). Left/click positions are routed to on_click and keystrokes to
    on_key; the screen is redrawn every frame. This is the blocking GUI loop
    - untested by design (same category as GameWindow.run / Img.show_frame);
    the screens' own logic is unit-tested without it."""
    clicks: list[tuple[int, int]] = []

    def _on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((x, y))

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT)
    cv2.setMouseCallback(window_name, _on_mouse)

    while True:
        while clicks:
            screen.on_click(*clicks.pop(0))

        canvas = Img().blank(theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT, theme.BACKGROUND_COLOR)
        screen.render(canvas)
        canvas.show_frame(window_name)

        outcome = screen.result()
        if outcome is not None:
            return outcome

        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == _ESC_KEY:
            return None
        if key != _NO_KEY:
            screen.on_key(key)

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            return None  # the window was closed
