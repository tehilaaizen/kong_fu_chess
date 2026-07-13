from pieces.piece import PieceRules, sliding_destinations, sliding_path_is_clear

ORTHOGONAL_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Rook(PieceRules):
    letter = "R"

    def can_move(self, d_row, d_col, color):
        return d_row == 0 or d_col == 0

    def is_path_clear(self, start, end, board, color):
        return sliding_path_is_clear(start, end, board)

    def legal_destinations(self, board, piece):
        return sliding_destinations(board, piece.cell, piece.color, ORTHOGONAL_DIRECTIONS)
