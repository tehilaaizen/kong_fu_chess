from client.network_commands import NetworkCommands
from model.board import Board
from model.piece import Piece
from model.position import Position


class FakeConnection:
    def __init__(self) -> None:
        self.sent: list = []

    def send(self, message) -> None:
        self.sent.append(message)

    def poll(self) -> list:
        return []


def _board_with_rook_at_a1() -> Board:
    board = Board(width=8, height=8)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(7, 0)))
    return board


def test_request_move_sends_the_move_in_wire_notation():
    connection = FakeConnection()
    commands = NetworkCommands(connection, _board_with_rook_at_a1())

    commands.request_move(Position(7, 0), Position(5, 0))  # a1 -> a3

    assert connection.sent == [{"type": "make_move", "payload": {"move": "WRa1a3"}}]


def test_request_move_from_an_empty_source_sends_nothing():
    connection = FakeConnection()
    commands = NetworkCommands(connection, _board_with_rook_at_a1())

    commands.request_move(Position(4, 4), Position(4, 5))  # empty source

    assert connection.sent == []


def test_request_jump_sends_the_cell_in_wire_notation():
    connection = FakeConnection()
    commands = NetworkCommands(connection, _board_with_rook_at_a1())

    commands.request_jump(Position(7, 0))  # a1

    assert connection.sent == [{"type": "jump_request", "payload": {"cell": "a1"}}]
