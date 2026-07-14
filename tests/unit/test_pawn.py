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


def test_no_two_step_move_from_a_non_start_row_cell():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(4, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(2, 1) not in destinations


def test_white_pawn_may_move_two_rows_from_its_start_row():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(3, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 1) in destinations


def test_black_pawn_may_move_two_rows_from_its_start_row():
    board = Board(width=3, height=5)
    pawn = _place(board, "b", "P", Position(1, 1), id=1)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(3, 1) in destinations


def test_two_step_move_is_blocked_by_a_piece_on_the_intermediate_cell():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(3, 1), id=1)
    _place(board, "b", "P", Position(2, 1), id=2)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 1) not in destinations


def test_two_step_move_is_blocked_by_a_piece_on_the_destination_cell():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(3, 1), id=1)
    _place(board, "b", "P", Position(1, 1), id=2)

    destinations = Pawn().legal_destinations(board, pawn)

    assert Position(1, 1) not in destinations


def test_promotes_to_a_queen_on_reaching_the_last_row():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(0, 1), id=1)

    Pawn().on_piece_arrival(board, pawn)

    assert pawn.kind == "Q"


def test_does_not_promote_before_the_last_row():
    board = Board(width=3, height=5)
    pawn = _place(board, "w", "P", Position(1, 1), id=1)

    Pawn().on_piece_arrival(board, pawn)

    assert pawn.kind == "P"
