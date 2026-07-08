from pieces.bishop import Bishop
from pieces.king import King
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.piece import EMPTY_SQUARE
from pieces.queen import Queen
from pieces.rook import Rook

VALID_COLORS = {"w", "b"}

PIECE_TYPES = {piece.letter: piece for piece in (King(), Queen(), Rook(), Bishop(), Knight(), Pawn())}


def is_valid_token(token):
    if token == EMPTY_SQUARE:
        return True

    if len(token) != 2:
        return False

    return token[0] in VALID_COLORS and token[1] in PIECE_TYPES


def is_legal_move(start, end, piece_type, board, color):
    if start == end:
        return False

    piece = PIECE_TYPES.get(piece_type)
    if piece is None:
        return False

    d_row = end[0] - start[0]
    d_col = end[1] - start[1]

    if not piece.can_move(d_row, d_col, color):
        return False

    return piece.is_path_clear(start, end, board, color)


def travel_time(piece_type, start, end):
    return PIECE_TYPES[piece_type].travel_time(start, end)


def settle_token(piece_type, color, position, board):
    """The token a piece becomes once it arrives at position (e.g. a pawn
    reaching the last row becomes a queen); unchanged for every other case."""
    new_letter = PIECE_TYPES[piece_type].on_arrival(position, board, color)
    return color + (new_letter if new_letter is not None else piece_type)
