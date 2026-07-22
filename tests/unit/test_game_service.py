from application.game_service import INVALID_NOTATION, NO_SUCH_GAME, PAUSED, GameService
from application.game_session import NOT_YOUR_PIECE
from messaging.application_events import GameMoveAppliedEvent, GameStartedEvent

BOARD_TEXT = "\n".join(
    [
        "bK . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        "wR . . . . . . .",
    ]
)
LONG_ENOUGH_MS = 100_000


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event) -> None:
        self.events.append(event)


def _service_with_game():
    publisher = RecordingPublisher()
    service = GameService(publisher)
    service.create_session("g1", "alice", "bob", BOARD_TEXT)
    return service, publisher


def test_create_session_registers_it_and_publishes_game_started():
    service, publisher = _service_with_game()

    assert service.session("g1").game_id == "g1"
    assert publisher.events == [GameStartedEvent("g1", "alice", "bob")]


def test_handle_move_on_an_unknown_game_is_rejected():
    service = GameService(RecordingPublisher())

    result = service.handle_move("nope", "w", "WRa1a7")

    assert result.is_accepted is False
    assert result.reason == NO_SUCH_GAME


def test_handle_move_with_malformed_notation_is_rejected():
    service, _ = _service_with_game()

    result = service.handle_move("g1", "w", "not-a-move")

    assert result.is_accepted is False
    assert result.reason == INVALID_NOTATION


def test_black_cannot_move_a_white_piece():
    service, _ = _service_with_game()

    result = service.handle_move("g1", "b", "WRa1a7")

    assert result.is_accepted is False
    assert result.reason == NOT_YOUR_PIECE


def test_a_valid_move_is_accepted_and_resolved_by_a_tick():
    service, publisher = _service_with_game()

    accepted = service.handle_move("g1", "w", "WRa1a7")
    assert accepted.is_accepted is True

    service.tick("g1", LONG_ENOUGH_MS)

    assert any(isinstance(e, GameMoveAppliedEvent) for e in publisher.events)


def test_handle_jump_delegates_and_rejects_an_opponents_piece():
    service, _ = _service_with_game()

    assert service.handle_jump("g1", "w", "a1").is_accepted is True


def test_handle_jump_on_an_unknown_game_is_rejected():
    service = GameService(RecordingPublisher())

    result = service.handle_jump("nope", "w", "a1")

    assert result.is_accepted is False
    assert result.reason == NO_SUCH_GAME


def test_handle_jump_with_malformed_cell_is_rejected():
    service, _ = _service_with_game()

    result = service.handle_jump("g1", "w", "zzz")

    assert result.is_accepted is False
    assert result.reason == INVALID_NOTATION


def test_tick_on_an_unknown_game_is_a_no_op():
    service = GameService(RecordingPublisher())

    service.tick("nope", LONG_ENOUGH_MS)  # must not raise


def test_tick_all_advances_every_live_game():
    publisher = RecordingPublisher()
    service = GameService(publisher)
    service.create_session("g1", "a", "b", BOARD_TEXT)
    service.create_session("g2", "c", "d", BOARD_TEXT)
    service.handle_move("g1", "w", "WRa1a7")
    service.handle_move("g2", "w", "WRa1a7")

    service.tick_all(LONG_ENOUGH_MS)

    applied = [e for e in publisher.events if isinstance(e, GameMoveAppliedEvent)]
    assert {e.game_id for e in applied} == {"g1", "g2"}


def test_a_paused_game_rejects_moves_and_jumps():
    service, _ = _service_with_game()

    service.pause("g1")

    assert service.is_paused("g1") is True
    assert service.handle_move("g1", "w", "WRa1a7").reason == PAUSED
    assert service.handle_jump("g1", "w", "a1").reason == PAUSED


def test_resuming_a_game_lets_moves_through_again():
    service, _ = _service_with_game()
    service.pause("g1")

    service.resume("g1")

    assert service.is_paused("g1") is False
    assert service.handle_move("g1", "w", "WRa1a7").is_accepted is True


def test_tick_all_freezes_a_paused_game_but_not_others():
    publisher = RecordingPublisher()
    service = GameService(publisher)
    service.create_session("g1", "a", "b", BOARD_TEXT)
    service.create_session("g2", "c", "d", BOARD_TEXT)
    service.handle_move("g1", "w", "WRa1a7")
    service.handle_move("g2", "w", "WRa1a7")
    service.pause("g1")

    service.tick_all(LONG_ENOUGH_MS)

    # g2 resolved its move; g1 stayed frozen (no arrival for it)
    arrivals = [e for e in publisher.events if isinstance(e, GameMoveAppliedEvent)]
    assert [e.game_id for e in arrivals] == ["g2"]
