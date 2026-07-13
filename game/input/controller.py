class Controller:
    """Translates clicks into game commands. Does not decide chess
    legality, and does not mutate Board directly - that's
    RuleEngine/GameEngine's job."""

    def __init__(self, board, board_mapper, game_engine):
        self._board = board
        self._board_mapper = board_mapper
        self._game_engine = game_engine
        self.selected_cell = None

    def click(self, x, y):
        position = self._board_mapper.pixel_to_cell(x, y)

        if position is None:
            self.selected_cell = None
            return

        if self.selected_cell is None:
            if not self._board.is_empty(position):
                self.selected_cell = position
            return

        self._game_engine.request_move(self.selected_cell, position)
        self.selected_cell = None
