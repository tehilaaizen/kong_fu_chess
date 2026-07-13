from input.board_mapper import BoardMapper
from input.controller import Controller
from model.board import Board
from model.piece import Piece
from model.position import Position


class FakeGameEngine:
    """Test double for GameEngine - just records requested moves. Injected
    via the constructor, per CLAUDE.md's no-monkey-patching rule."""

    def __init__(self):
        self.requested_moves = []
        self.requested_jumps = []

    def request_move(self, source, destination):
        self.requested_moves.append((source, destination))

    def request_jump(self, position):
        self.requested_jumps.append(position)


def _controller_with_king_at(position):
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="K", cell=position))
    game_engine = FakeGameEngine()
    controller = Controller(board, BoardMapper(board), game_engine)
    return controller, game_engine


def test_first_click_on_a_piece_selects_it():
    controller, _ = _controller_with_king_at(Position(0, 0))

    controller.click(50, 50)

    assert controller.selected_cell == Position(0, 0)


def test_first_click_on_an_empty_cell_leaves_selection_empty():
    controller, _ = _controller_with_king_at(Position(0, 0))

    controller.click(150, 150)

    assert controller.selected_cell is None


def test_first_click_outside_the_board_does_nothing():
    controller, game_engine = _controller_with_king_at(Position(0, 0))

    controller.click(1000, 1000)

    assert controller.selected_cell is None
    assert game_engine.requested_moves == []


def test_second_click_sends_source_and_destination_to_the_engine():
    controller, game_engine = _controller_with_king_at(Position(0, 0))

    controller.click(50, 50)
    controller.click(150, 150)

    assert game_engine.requested_moves == [(Position(0, 0), Position(1, 1))]


def test_second_click_clears_selection_even_though_the_move_may_be_illegal():
    controller, _ = _controller_with_king_at(Position(0, 0))

    controller.click(50, 50)
    controller.click(150, 150)

    assert controller.selected_cell is None


def test_outside_click_with_a_selection_cancels_it_without_calling_the_engine():
    controller, game_engine = _controller_with_king_at(Position(0, 0))

    controller.click(50, 50)
    controller.click(1000, 1000)

    assert controller.selected_cell is None
    assert game_engine.requested_moves == []


def test_jump_sends_the_clicked_position_to_the_engine():
    controller, game_engine = _controller_with_king_at(Position(0, 0))

    controller.jump(50, 50)

    assert game_engine.requested_jumps == [Position(0, 0)]


def test_jump_outside_the_board_does_nothing():
    controller, game_engine = _controller_with_king_at(Position(0, 0))

    controller.jump(1000, 1000)

    assert game_engine.requested_jumps == []


def test_jump_does_not_touch_selection_state():
    controller, _ = _controller_with_king_at(Position(0, 0))
    controller.click(50, 50)

    controller.jump(150, 150)

    assert controller.selected_cell == Position(0, 0)
