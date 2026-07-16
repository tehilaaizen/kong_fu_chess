from input.commands import ClickCommand, JumpCommand, LocalCommandSender


class _FakeController:
    def __init__(self) -> None:
        self.click_calls: list = []
        self.jump_calls: list = []

    def click(self, x: int, y: int) -> None:
        self.click_calls.append((x, y))

    def jump(self, x: int, y: int) -> None:
        self.jump_calls.append((x, y))


def test_send_a_click_command_calls_controller_click():
    controller = _FakeController()
    sender = LocalCommandSender(controller)

    sender.send(ClickCommand(10, 20))

    assert controller.click_calls == [(10, 20)]
    assert controller.jump_calls == []


def test_send_a_jump_command_calls_controller_jump():
    controller = _FakeController()
    sender = LocalCommandSender(controller)

    sender.send(JumpCommand(30, 40))

    assert controller.jump_calls == [(30, 40)]
    assert controller.click_calls == []
