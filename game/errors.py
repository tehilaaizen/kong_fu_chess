ROW_WIDTH_MISMATCH = "ROW_WIDTH_MISMATCH"
UNKNOWN_TOKEN = "UNKNOWN_TOKEN"
EMPTY_BOARD = "EMPTY_BOARD"


class BoardValidationError(Exception):
    """Raised by Board.validate()/BoardParser.parse() for malformed board
    text. code is one of the constants above, printed as `ERROR <code>` by
    the CLI."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
