from client.reconnect_data import ReconnectData


def test_a_fresh_game_is_not_waiting():
    assert ReconnectData().status() is None


def test_an_opponent_leaving_starts_the_countdown():
    data = ReconnectData()

    data.opponent_left("alice", 30)

    assert data.status() == ("alice", 30)


def test_the_countdown_ticks_down_with_time():
    data = ReconnectData()
    data.opponent_left("alice", 30)

    data.advance(1000)

    assert data.status() == ("alice", 29)


def test_the_countdown_never_goes_below_zero():
    data = ReconnectData()
    data.opponent_left("alice", 1)

    data.advance(5000)

    assert data.status() == ("alice", 0)


def test_partial_seconds_round_up_so_the_number_only_hits_zero_at_the_end():
    data = ReconnectData()
    data.opponent_left("alice", 30)

    data.advance(500)  # half a second elapsed

    assert data.status() == ("alice", 30)  # still shows 30, not 29


def test_the_opponent_returning_clears_the_wait():
    data = ReconnectData()
    data.opponent_left("alice", 30)

    data.opponent_returned()

    assert data.status() is None


def test_advance_does_nothing_while_not_waiting():
    data = ReconnectData()

    data.advance(1000)  # must not raise or start a phantom countdown

    assert data.status() is None
