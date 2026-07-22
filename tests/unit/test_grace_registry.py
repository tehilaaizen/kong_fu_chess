from server.grace_registry import DEFAULT_GRACE_MS, GraceRegistry


class _Clock:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


def _registry(clock=None, **kwargs):
    return GraceRegistry(now_ms=clock or _Clock(), **kwargs)


def test_a_player_who_reconnects_in_time_is_taken_back():
    registry = _registry()
    registry.begin("alice", "g1", "w")

    entry = registry.take("alice")

    assert entry is not None
    assert entry.game_id == "g1"
    assert entry.color == "w"


def test_taking_an_unknown_player_returns_none():
    assert _registry().take("nobody") is None


def test_a_game_with_a_player_in_grace_is_waiting():
    registry = _registry()
    registry.begin("alice", "g1", "w")

    assert registry.game_is_waiting("g1") is True
    registry.take("alice")
    assert registry.game_is_waiting("g1") is False


def test_discarding_a_game_forgets_its_grace():
    registry = _registry()
    registry.begin("alice", "g1", "w")

    registry.discard_game("g1")

    assert registry.game_is_waiting("g1") is False
    assert registry.take("alice") is None


def test_a_player_past_the_window_expires():
    clock = _Clock()
    registry = _registry(clock)
    registry.begin("alice", "g1", "w")

    clock.now = DEFAULT_GRACE_MS
    expired = registry.expired()

    assert [e.username for e in expired] == ["alice"]
    # and having expired, they can no longer be taken back
    assert registry.take("alice") is None


def test_a_player_still_within_the_window_does_not_expire():
    clock = _Clock()
    registry = _registry(clock)
    registry.begin("alice", "g1", "w")

    clock.now = DEFAULT_GRACE_MS - 1

    assert registry.expired() == []


def test_grace_seconds_reports_the_window_in_seconds():
    assert _registry(grace_ms=20_000).grace_seconds == 20
