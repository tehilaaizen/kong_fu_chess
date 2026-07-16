import cv2

from game_window import GameWindow


class _FakeController:
    def __init__(self) -> None:
        self.click_calls: list = []

    def click(self, x: int, y: int) -> None:
        self.click_calls.append((x, y))


def _window(controller=None):
    return GameWindow(
        renderer=None,
        controller=controller or _FakeController(),
        game_engine=None,
        clock=None,
        registry=None,
    )


def test_on_snapshot_stores_the_latest_snapshot():
    window = _window()

    window.on_snapshot("a-snapshot")

    assert window._latest_snapshot == "a-snapshot"


def test_on_snapshot_overwrites_the_previous_snapshot():
    window = _window()

    window.on_snapshot("first")
    window.on_snapshot("second")

    assert window._latest_snapshot == "second"


def test_left_button_down_forwards_to_controller_click():
    controller = _FakeController()
    window = _window(controller)

    window._on_mouse_event(cv2.EVENT_LBUTTONDOWN, 150, 250, 0, None)

    assert controller.click_calls == [(150, 250)]


def test_other_mouse_events_are_ignored():
    controller = _FakeController()
    window = _window(controller)

    window._on_mouse_event(cv2.EVENT_MOUSEMOVE, 150, 250, 0, None)
    window._on_mouse_event(cv2.EVENT_LBUTTONUP, 150, 250, 0, None)

    assert controller.click_calls == []
