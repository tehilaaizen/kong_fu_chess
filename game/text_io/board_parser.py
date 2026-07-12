from errors import EMPTY_BOARD, ROW_WIDTH_MISMATCH, UNKNOWN_TOKEN, BoardValidationError
from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces import is_valid_token
from pieces.piece import EMPTY_SQUARE


class BoardParser:
    """Text I/O adapter: turns board notation text into a Board. Ported
    from the validation logic that used to live on Board itself."""

    @staticmethod
    def parse(text):
        rows = [line.split() for line in text.splitlines() if line.strip()]

        if not rows:
            raise BoardValidationError(EMPTY_BOARD)

        width = len(rows[0])
        for row in rows:
            if len(row) != width:
                raise BoardValidationError(ROW_WIDTH_MISMATCH)

            for token in row:
                if not is_valid_token(token):
                    raise BoardValidationError(UNKNOWN_TOKEN)

        return BoardParser._build_board(rows, width)

    @staticmethod
    def _build_board(rows, width):
        board = Board(width=width, height=len(rows))

        next_id = 0
        for row_index, row in enumerate(rows):
            for col_index, token in enumerate(row):
                if token == EMPTY_SQUARE:
                    continue

                color, kind = token[0], token[1]
                cell = Position(row_index, col_index)
                board.add_piece(Piece(id=next_id, color=color, kind=kind, cell=cell))
                next_id += 1

        return board
