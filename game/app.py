# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

from app_support import build_game_window
from client.local_game_adapter import LocalGameAdapter
from engine.game_engine import GameEngine
from input.board_mapper import BoardMapper
from input.controller import Controller
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser
from view.consts import DEFAULT_PLAYER_NAME_BY_COLOR

# Standard chess starting position, in this project's own board notation
# (text_io/board_parser.py).
STARTING_POSITION_TEXT = """\
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR"""


def main(player_name_by_color: dict[str, str] = DEFAULT_PLAYER_NAME_BY_COLOR) -> None:
    """Offline entry point: wire the in-process Controller/GameEngine stack
    behind a LocalGameAdapter and drive a live interactive window from it -
    no server involved. player_name_by_color overrides the HUD's default
    player names ("White"/"Black"); there is no in-game name-entry UI, so
    this is the only way to change them. The view half is built by
    app_support.build_game_window, shared with the online entry point."""
    board = BoardParser.parse(STARTING_POSITION_TEXT)
    rule_engine = RuleEngine()
    real_time_arbiter = RealTimeArbiter(board)
    game_engine = GameEngine(board, rule_engine, real_time_arbiter)
    board_mapper = BoardMapper(board)
    controller = Controller(board, board_mapper, game_engine)
    client = LocalGameAdapter(game_engine, controller)

    window = build_game_window(client, board_mapper, player_name_by_color)
    window.run()


if __name__ == "__main__":
    main()
