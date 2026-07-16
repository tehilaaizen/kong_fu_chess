from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.rook import Rook
from rules.rule_engine import (
    EMPTY_SOURCE,
    FRIENDLY_DESTINATION,
    ILLEGAL_PIECE_MOVE,
    OK,
    OUTSIDE_BOARD,
    RuleEngine,
)


def _rule_engine():
    return RuleEngine(piece_rules_by_kind={"R": Rook()})


def _board_with_rook(color="w", cell=Position(2, 2)):
    board = Board(width=5, height=5)
    board.add_piece(Piece(id=1, color=color, kind="R", cell=cell))
    return board


def test_rejects_a_destination_outside_the_board():
    board = _board_with_rook()

    validation = _rule_engine().validate_move(board, Position(2, 2), Position(2, 99))

    assert validation.is_valid is False
    assert validation.reason == OUTSIDE_BOARD


def test_rejects_a_source_outside_the_board():
    board = _board_with_rook()

    validation = _rule_engine().validate_move(board, Position(-1, 0), Position(2, 2))

    assert validation.is_valid is False
    assert validation.reason == OUTSIDE_BOARD


def test_rejects_an_empty_source():
    board = _board_with_rook()

    validation = _rule_engine().validate_move(board, Position(0, 0), Position(2, 3))

    assert validation.is_valid is False
    assert validation.reason == EMPTY_SOURCE


def test_rejects_a_friendly_occupied_destination():
    board = _board_with_rook()
    board.add_piece(Piece(id=2, color="w", kind="P", cell=Position(2, 3)))

    validation = _rule_engine().validate_move(board, Position(2, 2), Position(2, 3))

    assert validation.is_valid is False
    assert validation.reason == FRIENDLY_DESTINATION


def test_rejects_an_illegal_piece_move():
    board = _board_with_rook()

    validation = _rule_engine().validate_move(board, Position(2, 2), Position(3, 3))

    assert validation.is_valid is False
    assert validation.reason == ILLEGAL_PIECE_MOVE


def test_accepts_a_legal_move():
    board = _board_with_rook()

    validation = _rule_engine().validate_move(board, Position(2, 2), Position(2, 4))

    assert validation.is_valid is True
    assert validation.reason == OK


def test_legal_destinations_returns_the_pieces_own_moves():
    board = _board_with_rook()

    destinations = _rule_engine().legal_destinations(board, Position(2, 2))

    assert Position(2, 4) in destinations  # along a clear rank
    assert Position(3, 3) not in destinations  # a rook never moves diagonally


def test_legal_destinations_of_an_empty_cell_is_empty():
    board = _board_with_rook()

    assert _rule_engine().legal_destinations(board, Position(0, 0)) == set()
