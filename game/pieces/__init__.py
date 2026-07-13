from pieces.bishop import Bishop
from pieces.king import King
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.piece import EMPTY_SQUARE, PieceRules, TokenBoard
from pieces.queen import Queen
from pieces.rook import Rook

VALID_COLORS = {"w", "b"}

PIECE_TYPES: dict[str, PieceRules] = {
    piece.letter: piece for piece in (King(), Queen(), Rook(), Bishop(), Knight(), Pawn())
}


def is_valid_token(token: str) -> bool:
    """Whether token is a legal board cell: "." or a 2-char color+kind
    token (e.g. "wK")."""
    if token == EMPTY_SQUARE:
        return True

    if len(token) != 2:
        return False

    return token[0] in VALID_COLORS and token[1] in PIECE_TYPES


def is_legal_move(
    start: tuple[int, int], end: tuple[int, int], piece_type: str, board: TokenBoard, color: str
) -> bool:
    """Whether moving piece_type of the given color from start to end is
    legal on board: not a no-op, a real piece kind, matching that piece's
    shape, and an unobstructed path."""
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


def travel_time(piece_type: str, start: tuple[int, int], end: tuple[int, int]) -> int:
    """How many ms piece_type takes to travel from start to end."""
    return PIECE_TYPES[piece_type].travel_time(start, end)


def settle_token(piece_type: str, color: str, position: tuple[int, int], board: TokenBoard) -> str:
    """The token a piece becomes once it arrives at position (e.g. a pawn
    reaching the last row becomes a queen); unchanged for every other case."""
    new_letter = PIECE_TYPES[piece_type].on_arrival(position, board, color)
    return color + (new_letter if new_letter is not None else piece_type)
