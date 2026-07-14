# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import sys

from commands import CommandContext, execute_commands, parse_sections
from engine.game_engine import GameEngine
from errors import BoardValidationError
from input.board_mapper import BoardMapper
from input.controller import Controller
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser


def main() -> None:
    """Read a Board:/Commands: script from stdin and execute its commands
    through the same Controller/GameEngine/RealTimeArbiter stack the
    text-integration tests exercise - printing `ERROR <code>` instead if
    the board text is malformed."""
    lines = [line.strip() for line in sys.stdin.read().splitlines()]
    board_text, commands = parse_sections(lines)

    try:
        board = BoardParser.parse(board_text)
    except BoardValidationError as error:
        print(f"ERROR {error.code}")
        return

    rule_engine = RuleEngine()
    real_time_arbiter = RealTimeArbiter(board)
    game_engine = GameEngine(board, rule_engine, real_time_arbiter)
    controller = Controller(board, BoardMapper(board), game_engine)

    execute_commands(commands, CommandContext(board, controller, game_engine))


if __name__ == "__main__":
    main()
