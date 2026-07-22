import cv2

from game_window import RESIZE_DEBOUNCE_FRAMES, GameWindow
from input.commands import ClickCommand, JumpCommand


class _FakeClient:
    """A GameClient whose send() records commands - these tests only
    exercise mouse handling, so the other methods are never called."""

    def __init__(self, reconnect_status=None) -> None:
        self.sent: list = []
        self._reconnect_status = reconnect_status

    def send(self, command) -> None:
        self.sent.append(command)

    def reconnect_status(self) -> tuple[str, int] | None:
        return self._reconnect_status


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


class _FakeResizer:
    """Reports a fixed initial window size and records apply() calls."""

    def __init__(self) -> None:
        self.applied: list[tuple[int, int]] = []

    def current_window_size(self) -> tuple[int, int]:
        return (1200, 800)

    def apply(self, width: int, height: int) -> None:
        self.applied.append((width, height))


def _window(extractor=None, client=None, resizer=None):
    return GameWindow(
        board_renderer=None,
        piece_renderer=None,
        highlight_renderer=None,
        rest_overlay_renderer=None,
        extractor=extractor or _FakeExtractor(),
        client=client or _FakeClient(),
        clock=None,
        registry=None,
        score_renderer=None,
        score_data=None,
        moves_log_renderer=None,
        moves_log_data=None,
        player_panel_renderer=None,
        game_over_renderer=None,
        game_over_data=None,
        connection_lost_renderer=None,
        reconnect_renderer=None,
        resizer=resizer or _FakeResizer(),
    )


def test_left_button_down_sends_a_click_command():
    client = _FakeClient()
    window = _window(client=client)

    window._on_mouse_event(cv2.EVENT_LBUTTONDOWN, 150, 250, 0, None)

    assert client.sent == [ClickCommand(150, 250)]


def test_right_button_down_sends_a_jump_command():
    client = _FakeClient()
    window = _window(client=client)

    window._on_mouse_event(cv2.EVENT_RBUTTONDOWN, 150, 250, 0, None)

    assert client.sent == [JumpCommand(150, 250)]


def test_input_is_locked_while_an_opponent_is_reconnecting():
    client = _FakeClient(reconnect_status=("alice", 12))
    window = _window(client=client)

    window._on_mouse_event(cv2.EVENT_LBUTTONDOWN, 150, 250, 0, None)

    assert client.sent == []  # the click is ignored while the game is frozen


def test_other_mouse_events_are_ignored():
    client = _FakeClient()
    window = _window(client=client)

    window._on_mouse_event(cv2.EVENT_MOUSEMOVE, 150, 250, 0, None)
    window._on_mouse_event(cv2.EVENT_LBUTTONUP, 150, 250, 0, None)

    assert client.sent == []


def test_a_click_outside_the_board_is_not_sent():
    client = _FakeClient()
    window = _window(extractor=_OutsideBoardExtractor(), client=client)

    window._on_mouse_event(cv2.EVENT_LBUTTONDOWN, 9999, 9999, 0, None)

    assert client.sent == []


def test_a_resize_is_applied_only_after_the_new_size_holds_for_the_debounce_window():
    resizer = _FakeResizer()
    window = _window(resizer=resizer)

    for _ in range(RESIZE_DEBOUNCE_FRAMES - 1):
        window._note_window_size(1600, 1000)
    assert resizer.applied == []

    window._note_window_size(1600, 1000)

    assert resizer.applied == [(1600, 1000)]


def test_a_changing_size_restarts_the_debounce_count():
    resizer = _FakeResizer()
    window = _window(resizer=resizer)

    for _ in range(RESIZE_DEBOUNCE_FRAMES - 1):
        window._note_window_size(1600, 1000)
    window._note_window_size(1700, 1000)  # size changed before it settled
    for _ in range(RESIZE_DEBOUNCE_FRAMES - 1):
        window._note_window_size(1700, 1000)

    assert resizer.applied == [(1700, 1000)]


def test_an_unchanged_or_nonpositive_size_never_triggers_a_resize():
    resizer = _FakeResizer()
    window = _window(resizer=resizer)

    for _ in range(RESIZE_DEBOUNCE_FRAMES * 2):
        window._note_window_size(1200, 800)  # equals the committed startup size
        window._note_window_size(0, 0)  # minimized / not yet realized

    assert resizer.applied == []
