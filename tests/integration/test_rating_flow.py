from application.game_service import GameService
from application.rating_service import RatingService
from messaging.application_message_bus import ApplicationMessageBus
from persistence.in_memory.user_repository import InMemoryUserRepository

# White rook a1, lone black king a8 - a1->a8 captures the king in one move.
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


def _wired():
    """A bus with a GameService and a RatingService over an in-memory user
    store seeded with the two players - the same wiring build_server uses,
    minus the sockets."""
    bus = ApplicationMessageBus()
    service = GameService(bus)
    repo = InMemoryUserRepository()
    repo.create_user("alice", "hash")
    repo.create_user("bob", "hash")
    bus.subscribe(RatingService(repo).handle)
    return service, repo


def test_winning_by_king_capture_updates_both_players_ratings():
    service, repo = _wired()
    service.create_session("g1", "alice", "bob", BOARD_TEXT)

    service.handle_move("g1", "w", "WRa1a8")  # White rook takes the king
    service.tick("g1", LONG_ENOUGH_MS)

    assert repo.get_user("alice").rating == 1216  # White won
    assert repo.get_user("bob").rating == 1184


def test_winning_by_abandonment_updates_both_players_ratings():
    service, repo = _wired()
    session = service.create_session("g1", "alice", "bob", BOARD_TEXT)

    session.abandon("b")  # White left, Black wins by abandonment

    assert repo.get_user("bob").rating == 1216  # Black won
    assert repo.get_user("alice").rating == 1184
