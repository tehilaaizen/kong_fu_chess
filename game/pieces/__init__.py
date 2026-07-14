from __future__ import annotations

from pieces.bishop import Bishop
from pieces.king import King
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.piece import EMPTY_SQUARE, PieceRules
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
