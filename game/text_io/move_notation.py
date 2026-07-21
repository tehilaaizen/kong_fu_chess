from __future__ import annotations

from dataclasses import dataclass

from model.position import Position
from pieces import PIECE_TYPES, VALID_COLORS

MOVE_LENGTH = 6


class InvalidMoveNotation(ValueError):
    """Raised when a move string is not well-formed "WQe2e5" notation
    (wrong length, unknown color/kind, or a non-algebraic cell)."""


@dataclass(frozen=True)
class ParsedMove:
    """One move parsed off the wire: the moving piece's color ("w"/"b")
    and kind ("K"/"Q"/"R"/"B"/"N"/"P") as stated by the sender, plus the
    source and destination cells. GameService validates color/kind against
    the piece actually at source before trusting the move."""

    color: str
    kind: str
    source: Position
    destination: Position


class MoveNotation:
    """Parses the wire move notation "WQe2e5" - color, kind, source cell,
    destination cell - into board Positions. This is the only place that
    knows the algebraic<->(row, col) mapping, keeping it out of the server
    and application layers (the same seam BoardParser is for board text).

    Algebraic files a..h map to columns 0.. left-to-right. Ranks are
    flipped: this board puts row 0 at the top (black's back rank in the
    standard start layout), so rank 1 is the bottom row and rank N the
    top - row = board_height - rank."""

    @staticmethod
    def parse(move: str, board_height: int) -> ParsedMove:
        """Parse a "WQe2e5"-style move against a board board_height rows
        tall. Raises InvalidMoveNotation on any structural problem; cells
        that are syntactically valid but off the board are left for the
        rule layer to reject via Board.in_bounds."""
        if len(move) != MOVE_LENGTH:
            raise InvalidMoveNotation(f"move must be {MOVE_LENGTH} characters, got {move!r}")

        color = move[0].lower()
        if color not in VALID_COLORS:
            raise InvalidMoveNotation(f"unknown color in {move!r}")

        kind = move[1].upper()
        if kind not in PIECE_TYPES:
            raise InvalidMoveNotation(f"unknown piece kind in {move!r}")

        source = MoveNotation._cell(move[2:4], board_height, move)
        destination = MoveNotation._cell(move[4:6], board_height, move)

        return ParsedMove(color=color, kind=kind, source=source, destination=destination)

    @staticmethod
    def parse_cell(cell: str, board_height: int) -> Position:
        """Convert a lone algebraic cell like "e2" to a Position - used
        for a jump command, which targets one cell rather than a move.
        Raises InvalidMoveNotation if cell isn't a two-character
        file+rank."""
        if len(cell) != 2:
            raise InvalidMoveNotation(f"cell must be 2 characters, got {cell!r}")
        return MoveNotation._cell(cell, board_height, cell)

    @staticmethod
    def format(color: str, kind: str, source: Position, destination: Position, board_height: int) -> str:
        """Encode a move back into "WRa1a7" notation - the inverse of
        parse, so a client that resolved a click into (source, destination)
        can name the move for the wire. Color and kind are upper-cased to
        the canonical wire form."""
        return (
            color.upper()
            + kind.upper()
            + MoveNotation.format_cell(source, board_height)
            + MoveNotation.format_cell(destination, board_height)
        )

    @staticmethod
    def format_cell(position: Position, board_height: int) -> str:
        """Encode one Position as an algebraic cell like "e2" - the inverse
        of parse_cell, flipping the rank back (rank = board_height - row)."""
        file_char = chr(ord("a") + position.col)
        rank = board_height - position.row
        return f"{file_char}{rank}"

    @staticmethod
    def _cell(cell: str, board_height: int, move: str) -> Position:
        """Convert one algebraic cell like "e2" to a Position, flipping the
        rank so rank 1 is the bottom row (row = board_height - rank)."""
        file_char, rank_char = cell[0], cell[1]
        if not file_char.isalpha() or not rank_char.isdigit():
            raise InvalidMoveNotation(f"invalid cell {cell!r} in {move!r}")

        col = ord(file_char.lower()) - ord("a")
        row = board_height - int(rank_char)
        return Position(row, col)
