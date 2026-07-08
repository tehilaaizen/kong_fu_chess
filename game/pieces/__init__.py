from pieces.bishop import Bishop
from pieces.king import King
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.queen import Queen
from pieces.rook import Rook

VALID_COLORS = {"w", "b"}
EMPTY_SQUARE = "."

PIECE_TYPES = {piece.letter: piece for piece in (King(), Queen(), Rook(), Bishop(), Knight(), Pawn())}


def is_valid_token(token):
    if token == EMPTY_SQUARE:
        return True

    if len(token) != 2:
        return False

    return token[0] in VALID_COLORS and token[1] in PIECE_TYPES


def is_legal_move(start, end, piece_type):
    if start == end:
        return False

    piece = PIECE_TYPES.get(piece_type)
    if piece is None:
        return False

    d_row = abs(end[0] - start[0])
    d_col = abs(end[1] - start[1])

    return piece.can_move(d_row, d_col)
