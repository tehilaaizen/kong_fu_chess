import sys

from board import Board
from commands import execute_commands, parse_sections
from errors import BoardValidationError
from session import GameSession


def main():
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
