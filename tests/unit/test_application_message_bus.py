import logging

from messaging.application_message_bus import ApplicationMessageBus


def test_a_subscriber_receives_published_events_in_order():
    bus = ApplicationMessageBus()
    received: list = []
    bus.subscribe(received.append)

    bus.publish("a")
    bus.publish("b")

    assert received == ["a", "b"]


def test_every_subscriber_receives_each_event():
    bus = ApplicationMessageBus()
    first: list = []
    second: list = []
    bus.subscribe(first.append)
    bus.subscribe(second.append)

    bus.publish("x")

    assert first == ["x"]
    assert second == ["x"]


def test_a_handler_that_raises_is_isolated_and_logged(caplog):
    bus = ApplicationMessageBus()
    delivered: list = []

    def boom(event) -> None:
        raise ValueError("handler blew up")

    bus.subscribe(boom)
    bus.subscribe(delivered.append)

    with caplog.at_level(logging.ERROR):
        bus.publish("still-delivered")

    assert delivered == ["still-delivered"]  # the good handler still ran
    assert "handler failed" in caplog.text


def test_publishing_with_no_subscribers_is_a_no_op():
    ApplicationMessageBus().publish("nobody-listening")  # must not raise
