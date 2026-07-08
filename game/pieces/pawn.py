from pieces.piece import EMPTY_SQUARE, Piece

FORWARD_DIRECTION = {"w": -1, "b": 1}


class Pawn(Piece):
    letter = "P"

    def can_move(self, d_row, d_col, color):
        direction = FORWARD_DIRECTION[color]
        return d_row == direction and abs(d_col) <= 1

    def is_path_clear(self, start, end, board):
        d_col = end[1] - start[1]
        destination = board.token_at(end[0], end[1])

        if d_col == 0:
            return destination == EMPTY_SQUARE  # straight move: only onto an empty cell

        return destination != EMPTY_SQUARE  # diagonal move: only as a capture
