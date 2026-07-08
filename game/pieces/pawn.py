from pieces.piece import Piece


class Pawn(Piece):
    letter = "P"

    def can_move(self, d_row, d_col):
        return True  # placeholder until pawn movement is implemented
