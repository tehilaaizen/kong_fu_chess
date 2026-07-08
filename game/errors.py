ROW_WIDTH_MISMATCH = "ROW_WIDTH_MISMATCH"
UNKNOWN_TOKEN = "UNKNOWN_TOKEN"
EMPTY_BOARD = "EMPTY_BOARD"


class BoardValidationError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code
