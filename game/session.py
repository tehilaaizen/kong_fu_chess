from dataclasses import dataclass

from pieces import EMPTY_SQUARE, is_legal_move, settle_token, travel_time
from pieces.king import King

CELL_SIZE = 100
JUMP_DURATION_MS = 1000


@dataclass
class PendingMove:
    source: tuple
    destination: tuple
    token: str
    arrival_time: int


@dataclass
class Jump:
    cell: tuple
    until_time: int


class GameSession:
    """The live, mutable state of one game: the board, the current
    selection, the game clock, moves still travelling, and pieces airborne
    from a jump."""

    def __init__(self, board):
        self.board = board
        self.selected_cell = None
        self.clock_ms = 0
        self.pending_moves = []
        self.jumps = []
        self.game_over = False

    def advance_clock(self, ms):
        self.clock_ms += ms
        self._settle_pending_moves()
        self._expire_jumps()

    def click(self, x, y):
        self._settle_pending_moves()
        self._expire_jumps()

        if self.game_over:
            return

        if self.pending_moves:
            return  # the common route is occupied - no clicks accepted until it clears

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
        color = selected_token[0]
        if is_legal_move((sel_row, sel_col), (row, col), piece_type, self.board, color):
            self._schedule_move((sel_row, sel_col), (row, col), selected_token)

        self.selected_cell = None

    def jump(self, x, y):
        self._settle_pending_moves()
        self._expire_jumps()

        if self.game_over or self.pending_moves:
            return  # a moving piece cannot jump

        row, col = y // CELL_SIZE, x // CELL_SIZE

        if not (0 <= row < self.board.height and 0 <= col < self.board.width):
            return

        cell = (row, col)

        if self.board.token_at(row, col) == EMPTY_SQUARE:
            return  # a captured (or nonexistent) piece cannot jump

        if self._is_airborne(cell):
            return

        self.jumps.append(Jump(cell, self.clock_ms + JUMP_DURATION_MS))

    def _is_airborne(self, cell):
        return any(jump.cell == cell for jump in self.jumps)

    def _clear_airborne(self, cell):
        self.jumps = [jump for jump in self.jumps if jump.cell != cell]

    def _expire_jumps(self):
        self.jumps = [jump for jump in self.jumps if jump.until_time > self.clock_ms]

    def _schedule_move(self, source, destination, token):
        duration = travel_time(token[1], source, destination)
        self.pending_moves.append(PendingMove(source, destination, token, self.clock_ms + duration))

    def _settle_pending_moves(self):
        still_pending = []

        for move in self.pending_moves:
            if move.arrival_time > self.clock_ms:
                still_pending.append(move)
                continue

            if self._is_airborne(move.destination):
                # the airborne defender destroys the arriving piece and stays put
                self._clear_airborne(move.destination)
                self.board.rows[move.source[0]][move.source[1]] = EMPTY_SQUARE
                continue

            captured = self.board.token_at(*move.destination)
            if captured != EMPTY_SQUARE and captured[1] == King.letter:
                self.game_over = True

            color, piece_type = move.token[0], move.token[1]
            final_token = settle_token(piece_type, color, move.destination, self.board)

            self.board.rows[move.destination[0]][move.destination[1]] = final_token
            self.board.rows[move.source[0]][move.source[1]] = EMPTY_SQUARE

        self.pending_moves = still_pending
