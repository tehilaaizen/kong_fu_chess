from errors import EMPTY_BOARD, ROW_WIDTH_MISMATCH, UNKNOWN_TOKEN, BoardValidationError
from pieces import is_valid_token


class Board:
    """Legacy token-grid board used by the original CLI pipeline
    (session.py/commands.py/game.py). Superseded by model.board.Board for
    the layered architecture; kept until session.py migrates to it."""

    def __init__(self, rows: list[list[str]]) -> None:
        self.rows = rows

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    @property
    def height(self) -> int:
        return len(self.rows)

    def token_at(self, row: int, col: int) -> str:
        return self.rows[row][col]

    def validate(self) -> None:
        """Raise BoardValidationError if rows is empty, has inconsistent
        row widths, or contains an unknown token."""
        if not self.rows:
            raise BoardValidationError(EMPTY_BOARD)

        width = self.width
        for row in self.rows:
            if len(row) != width:
                raise BoardValidationError(ROW_WIDTH_MISMATCH)

            for token in row:
                if not is_valid_token(token):
                    raise BoardValidationError(UNKNOWN_TOKEN)

    def to_text(self) -> str:
        """Render rows back to the same row-per-line, space-separated
        notation the input was parsed from."""
        return "\n".join(" ".join(row) for row in self.rows)
