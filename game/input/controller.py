from typing import Protocol

from input.board_mapper import BoardMapper
from model.board import Board
from model.position import Position


class RequestsMoves(Protocol):
    """The only capability Controller needs from a game engine - lets
    tests inject a lightweight fake instead of the real GameEngine."""

    def request_move(self, source: Position, destination: Position) -> object:
        ...


class Controller:
    """Translates clicks into game commands. Does not decide chess
    legality, and does not mutate Board directly - that's
    RuleEngine/GameEngine's job."""

    def __init__(self, board: Board, board_mapper: BoardMapper, game_engine: RequestsMoves) -> None:
        """board and board_mapper are used read-only; game_engine
        receives move requests (any object with a request_move method)."""
        self._board = board
        self._board_mapper = board_mapper
        self._game_engine = game_engine
        self.selected_cell: Position | None = None

    def click(self, x: int, y: int) -> None:
        """Handle one click: select a piece on the first in-board click,
        or request a move (and clear selection) on the second. An
        outside-board click cancels any active selection."""
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
