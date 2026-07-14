from engine.game_snapshot import GameSnapshot
from model.board import Board
from model.piece import Piece
from model.position import Position


def test_from_board_copies_board_dimensions():
    board = Board(width=4, height=6)

    snapshot = GameSnapshot.from_board(board)

    assert snapshot.board_width == 4
    assert snapshot.board_height == 6


def test_from_board_is_empty_for_an_empty_board():
    board = Board(width=3, height=3)

    snapshot = GameSnapshot.from_board(board)

    assert snapshot.pieces == []


def test_from_board_includes_each_pieces_kind_color_and_cell():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="K", cell=Position(0, 0)))
    board.add_piece(Piece(id=2, color="b", kind="R", cell=Position(2, 2)))

    snapshot = GameSnapshot.from_board(board)

    placements = {(p.kind, p.color, p.cell) for p in snapshot.pieces}
    assert placements == {("K", "w", Position(0, 0)), ("R", "b", Position(2, 2))}
