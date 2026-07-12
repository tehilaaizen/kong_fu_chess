from model.board import Board
from model.piece import Piece
from model.position import Position
from text_io.board_printer import BoardPrinter


def test_prints_board_rows_as_space_separated_text():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="K", cell=Position(0, 0)))
    board.add_piece(Piece(id=2, color="w", kind="R", cell=Position(1, 1)))
    board.add_piece(Piece(id=3, color="b", kind="K", cell=Position(2, 2)))

    assert BoardPrinter.to_text(board) == "wK . .\n. wR .\n. . bK"


def test_prints_a_fully_empty_board():
    board = Board(width=2, height=2)

    assert BoardPrinter.to_text(board) == ". .\n. ."
