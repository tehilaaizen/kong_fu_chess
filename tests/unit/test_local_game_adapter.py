from client.local_game_adapter import LocalGameAdapter
from input.commands import ClickCommand, JumpCommand
from model.position import Position


class _FakeEngine:
    def __init__(self) -> None:
        self.waited: list[int] = []
        self.observers: list = []
        self.snapshot_value = "SNAP"
        self.destinations = {Position(0, 1)}

    def wait(self, ms):
        self.waited.append(ms)

    def snapshot(self):
        return self.snapshot_value

    def legal_destinations(self, source):
        return self.destinations

    def add_observer(self, observer):
        self.observers.append(observer)


class _FakeController:
    def __init__(self) -> None:
        self.selected_cell = Position(2, 2)
        self.clicks: list = []
        self.jumps: list = []

    def click(self, x, y):
        self.clicks.append((x, y))

    def jump(self, x, y):
        self.jumps.append((x, y))


def _adapter():
    engine = _FakeEngine()
    controller = _FakeController()
    return LocalGameAdapter(engine, controller), engine, controller


def test_snapshot_delegates_to_the_engine():
    adapter, engine, _ = _adapter()

    assert adapter.snapshot() == engine.snapshot_value


def test_advance_steps_the_engines_simulated_time():
    adapter, engine, _ = _adapter()

    adapter.advance(250)

    assert engine.waited == [250]


def test_legal_destinations_delegates_to_the_engine():
    adapter, engine, _ = _adapter()

    assert adapter.legal_destinations(Position(0, 0)) == engine.destinations


def test_add_observer_forwards_to_the_engine():
    adapter, engine, _ = _adapter()
    observer = object()

    adapter.add_observer(observer)

    assert engine.observers == [observer]


def test_selected_cell_reads_the_controller():
    adapter, _, controller = _adapter()

    assert adapter.selected_cell == controller.selected_cell


def test_send_routes_a_click_command_to_the_controller():
    adapter, _, controller = _adapter()

    adapter.send(ClickCommand(150, 250))

    assert controller.clicks == [(150, 250)]


def test_send_routes_a_jump_command_to_the_controller():
    adapter, _, controller = _adapter()

    adapter.send(JumpCommand(30, 40))

    assert controller.jumps == [(30, 40)]


def test_connection_is_never_lost_for_local_play():
    adapter, _, _ = _adapter()

    assert adapter.connection_lost() is False
