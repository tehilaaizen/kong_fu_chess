from pieces import EMPTY_SQUARE, is_legal_move

CELL_SIZE = 100


class GameSession:
    """The live, mutable state of one game: the board, the current
    selection, and the game clock."""

    def __init__(self, board):
        self.board = board
        self.selected_cell = None
        self.clock_ms = 0

    def advance_clock(self, ms):
        self.clock_ms += ms

    def click(self, x, y):
        row, col = y // CELL_SIZE, x // CELL_SIZE

        if not (0 <= row < self.board.height and 0 <= col < self.board.width):
            return

        clicked_token = self.board.rows[row][col]

        if self.selected_cell is None:
            if clicked_token != EMPTY_SQUARE:
                self.selected_cell = (row, col)
            return

        sel_row, sel_col = self.selected_cell
        selected_token = self.board.rows[sel_row][sel_col]

        if clicked_token != EMPTY_SQUARE and clicked_token[0] == selected_token[0]:
            self.selected_cell = (row, col)
            return

        piece_type = selected_token[1]
        if is_legal_move((sel_row, sel_col), (row, col), piece_type):
            self.board.rows[row][col] = selected_token
            self.board.rows[sel_row][sel_col] = EMPTY_SQUARE

        self.selected_cell = None
