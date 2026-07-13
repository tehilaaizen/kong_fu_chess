# Repo: https://github.com/tehilaaizen/kong_fu_chess

import sys

from board import Board
from commands import execute_commands, parse_sections
from errors import BoardValidationError
from session import GameSession


def main() -> None:
    """Read a Board:/Commands: script from stdin, validate the board, and
    execute its commands - printing `ERROR <code>` instead if the board
    text is malformed."""
    lines = [line.strip() for line in sys.stdin.read().splitlines()]
    board_rows, commands = parse_sections(lines)
    board = Board(board_rows)

    try:
        board.validate()
    except BoardValidationError as error:
        print(f"ERROR {error.code}")
        return

    session = GameSession(board)
    execute_commands(commands, session)


if __name__ == "__main__":
    main()
