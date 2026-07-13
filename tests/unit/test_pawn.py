from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.pawn import Pawn


def _place(board, color, kind, cell, id):
    piece = Piece(id=id, color=color, kind=kind, cell=cell)
    board.add_piece(piece)
    return piece


def test_white_pawn_moves_one_row_upward_onto_an_empty_cell():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(2, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 1) in destinations


def test_black_pawn_moves_one_row_downward_onto_an_empty_cell():
    board = Board(width=3, height=5)
    pawn = _place(board, "b", "P", Position(2, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(3, 1) in destinations


def test_forward_move_is_blocked_by_any_piece():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(2, 1), id=1)
    _place(board, "b", "P", Position(1, 1), id=2)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 1) not in destinations


def test_captures_diagonally_only_when_an_enemy_is_present():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(2, 1), id=1)
    _place(board, "b", "P", Position(1, 0), id=2)
    _place(board, "b", "P", Position(1, 2), id=3)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 0) in destinations
    assert Position(1, 2) in destinations


def test_does_not_capture_diagonally_onto_an_empty_cell():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(2, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 0) not in destinations
    assert Position(1, 2) not in destinations


def test_does_not_capture_diagonally_onto_a_friendly_piece():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(2, 1), id=1)
    _place(board, "w", "P", Position(1, 0), id=2)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 0) not in destinations


def test_has_no_two_step_start_move():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(4, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(2, 1) not in destinations
