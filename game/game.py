import sys

from board import Board
from commands import execute_commands, parse_sections
from errors import BoardValidationError


def main():
    lines = [line.strip() for line in sys.stdin.read().splitlines()]
    board_rows, commands = parse_sections(lines)
    board = Board(board_rows)

    try:
        board.validate()
    except BoardValidationError as error:
        print(f"ERROR {error.code}")
        return

    execute_commands(commands, board)


if __name__ == "__main__":
    main()
