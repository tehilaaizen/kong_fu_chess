# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

from engine.game_engine import GameEngine
from game_window import GameWindow
from input.board_mapper import BoardMapper
from input.controller import Controller
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser
from view.frame_clock import FrameClock
from view.piece_animator_registry import PieceAnimatorRegistry
from view.renderer import Renderer

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


def main() -> None:
    """Wire up the same Controller/GameEngine/RealTimeArbiter stack as
    game.py's text-DSL entry point, but drive it from a live interactive
    window instead of stdin commands."""
    board = BoardParser.parse(STARTING_POSITION_TEXT)
    rule_engine = RuleEngine()
    real_time_arbiter = RealTimeArbiter(board)
    game_engine = GameEngine(board, rule_engine, real_time_arbiter)
    controller = Controller(board, BoardMapper(board), game_engine)

    window = GameWindow(
        renderer=Renderer(),
        controller=controller,
        game_engine=game_engine,
        clock=FrameClock(),
        registry=PieceAnimatorRegistry(),
    )
    game_engine.add_observer(window)
    window.run()


if __name__ == "__main__":
    main()
