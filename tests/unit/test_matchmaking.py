from server.matchmaking import DEFAULT_TIMEOUT_MS, MatchmakingService, Pairing, _monotonic_ms


class _Clock:
    """A hand-driven clock so timeout tests advance time without sleeping."""

    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


def _service(clock=None, **kwargs):
    return MatchmakingService(now_ms=clock or _Clock(), **kwargs)


def test_the_default_clock_returns_a_millisecond_reading():
    assert isinstance(_monotonic_ms(), int)


def test_the_first_player_waits_and_is_not_matched():
    service = _service()

    assert service.request_match("c1", 1200) is None


def test_two_players_in_range_are_paired_first_waiter_as_white():
    service = _service()
    service.request_match("c1", 1200)

    pairing = service.request_match("c2", 1250)

    assert pairing == Pairing(white_id="c1", black_id="c2")


def test_players_out_of_range_are_not_paired():
    service = _service(elo_range=100)
    service.request_match("c1", 1200)

    # 1400 is 200 above 1200 - outside the +/-100 window
    assert service.request_match("c2", 1400) is None


def test_the_closest_rated_waiting_player_is_chosen():
    service = _service(elo_range=100)
    service.request_match("c1", 1120)  # 80 away from 1200
    service.request_match("c2", 1250)  # 50 away from 1200 - both within 100

    pairing = service.request_match("c3", 1200)

    assert pairing.white_id == "c2"  # 1250 is closer to 1200 than 1120 is
    assert pairing.black_id == "c3"


def test_a_cancelled_player_is_no_longer_matchable():
    service = _service()
    service.request_match("c1", 1200)

    assert service.cancel("c1") is True
    assert service.request_match("c2", 1200) is None  # c1 is gone, so c2 waits


def test_cancelling_a_player_who_is_not_queued_returns_false():
    assert _service().cancel("ghost") is False


def test_re_requesting_while_queued_does_not_duplicate():
    service = _service()
    service.request_match("c1", 1200)
    service.request_match("c1", 1200)  # same player asks again

    # a single opponent should pair with c1 and leave the queue empty
    service.request_match("c2", 1200)
    assert service.request_match("c3", 1200) is None  # queue empty again, c3 waits


def test_a_player_times_out_after_the_timeout_window():
    clock = _Clock()
    service = _service(clock)
    service.request_match("c1", 1200)

    clock.now = DEFAULT_TIMEOUT_MS
    assert service.expire() == ["c1"]
    # and having expired, c1 is no longer in the queue to match
    assert service.request_match("c2", 1200) is None


def test_a_player_still_within_the_window_does_not_time_out():
    clock = _Clock()
    service = _service(clock)
    service.request_match("c1", 1200)

    clock.now = DEFAULT_TIMEOUT_MS - 1
    assert service.expire() == []
