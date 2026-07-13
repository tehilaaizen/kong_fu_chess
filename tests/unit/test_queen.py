from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.rook import Rook


def _place(board, color, kind, cell, id):
    piece = Piece(id=id, color=color, kind=kind, cell=cell)
    board.add_piece(piece)
    return piece


def test_legal_destinations_are_rook_plus_bishop():
    board = Board(width=5, height=5)
    queen = _place(board, "w", "Q", Position(2, 2), id=1)

    destinations = Queen().legal_destinations(board, queen)

    rook_destinations = Rook().legal_destinations(board, queen)
    bishop_destinations = Bishop().legal_destinations(board, queen)
    assert destinations == rook_destinations | bishop_destinations
    assert Position(2, 4) in destinations  # straight line
    assert Position(4, 4) in destinations  # diagonal


def test_stops_before_a_friendly_blocker_in_either_direction():
    board = Board(width=5, height=5)
    queen = _place(board, "w", "Q", Position(2, 2), id=1)
    _place(board, "w", "P", Position(2, 4), id=2)
    _place(board, "w", "P", Position(4, 4), id=3)

    destinations = Queen().legal_destinations(board, queen)

    assert Position(2, 3) in destinations
    assert Position(2, 4) not in destinations
    assert Position(3, 3) in destinations
    assert Position(4, 4) not in destinations
