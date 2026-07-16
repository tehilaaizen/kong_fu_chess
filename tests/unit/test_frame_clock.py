from view.frame_clock import FrameClock


def _fake_time_source(values: list):
    iterator = iter(values)
    return lambda: next(iterator)


def test_tick_ms_is_zero_immediately_after_construction():
    clock = FrameClock(time_source=_fake_time_source([0.0, 0.0]))

    assert clock.tick_ms() == 0


def test_tick_ms_measures_elapsed_time_since_the_previous_call():
    clock = FrameClock(time_source=_fake_time_source([0.0, 0.5, 0.8]))

    assert clock.tick_ms() == 500
    assert clock.tick_ms() == 300


def test_now_ms_never_resets_between_calls():
    clock = FrameClock(time_source=_fake_time_source([0.0, 0.5, 1.2]))

    assert clock.now_ms() == 500
    assert clock.now_ms() == 1200


def test_tick_ms_and_now_ms_are_independent():
    clock = FrameClock(time_source=_fake_time_source([0.0, 0.4, 0.9]))

    assert clock.tick_ms() == 400
    assert clock.now_ms() == 900
