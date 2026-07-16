import cv2

from game_window import GameWindow
from input.commands import ClickCommand, JumpCommand


class _FakeCommandSender:
    def __init__(self) -> None:
        self.sent: list = []

    def send(self, command) -> None:
        self.sent.append(command)


class _FakeExtractor:
    """Always resolves to a command at the given pixel - mirrors a click
    that always lands inside the board."""

    def extract_left_click(self, x: int, y: int) -> ClickCommand:
        return ClickCommand(x, y)

    def extract_right_click(self, x: int, y: int) -> JumpCommand:
        return JumpCommand(x, y)


class _OutsideBoardExtractor:
    """Always resolves to None - mirrors a click that lands outside the
    board (e.g. on a future HUD sidebar)."""

    def extract_left_click(self, x: int, y: int) -> None:
        return None

    def extract_right_click(self, x: int, y: int) -> None:
        return None


def _window(extractor=None, command_sender=None):
    return GameWindow(
        board_renderer=None,
        piece_renderer=None,
        extractor=extractor or _FakeExtractor(),
        command_sender=command_sender or _FakeCommandSender(),
        game_engine=None,
        clock=None,
        registry=None,
        score_renderer=None,
        score_data=None,
        moves_log_renderer=None,
        moves_log_data=None,
        player_panel_renderer=None,
    )


def test_left_button_down_sends_a_click_command():
    sender = _FakeCommandSender()
    window = _window(command_sender=sender)

    window._on_mouse_event(cv2.EVENT_LBUTTONDOWN, 150, 250, 0, None)

    assert sender.sent == [ClickCommand(150, 250)]


def test_right_button_down_sends_a_jump_command():
    sender = _FakeCommandSender()
    window = _window(command_sender=sender)

    window._on_mouse_event(cv2.EVENT_RBUTTONDOWN, 150, 250, 0, None)

    assert sender.sent == [JumpCommand(150, 250)]


def test_other_mouse_events_are_ignored():
    sender = _FakeCommandSender()
    window = _window(command_sender=sender)

    window._on_mouse_event(cv2.EVENT_MOUSEMOVE, 150, 250, 0, None)
    window._on_mouse_event(cv2.EVENT_LBUTTONUP, 150, 250, 0, None)

    assert sender.sent == []


def test_a_click_outside_the_board_is_not_sent():
    sender = _FakeCommandSender()
    window = _window(extractor=_OutsideBoardExtractor(), command_sender=sender)

    window._on_mouse_event(cv2.EVENT_LBUTTONDOWN, 9999, 9999, 0, None)

    assert sender.sent == []
