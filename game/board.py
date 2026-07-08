from errors import BoardValidationError, ROW_WIDTH_MISMATCH, UNKNOWN_TOKEN, EMPTY_BOARD
from piece_token import is_valid_token


class Board:
    def __init__(self, rows):
        self.rows = rows

    @property
    def width(self):
        return len(self.rows[0]) if self.rows else 0

    @property
    def height(self):
        return len(self.rows)

    def validate(self):
        if not self.rows:
            raise BoardValidationError(EMPTY_BOARD)

        width = self.width
        for row in self.rows:
            if len(row) != width:
                raise BoardValidationError(ROW_WIDTH_MISMATCH)

            for token in row:
                if not is_valid_token(token):
                    raise BoardValidationError(UNKNOWN_TOKEN)

    def to_text(self):
        return "\n".join(" ".join(row) for row in self.rows)
