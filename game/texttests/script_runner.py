from model.board import Board
from text_io.board_parser import BoardParser
from text_io.board_printer import BoardPrinter
from texttests.script_parser import parse_script

PRINT_BOARD_COMMAND = "print board"


class ScriptAssertionError(AssertionError):
    """Raised when a `print board` command's actual output does not match
    the expected rows embedded in the script."""


def run_script(text: str) -> None:
    """Executes a .kfc integration-test script, asserting every `print
    board` against the expected rows that follow it in the script."""
    board_text, command_blocks = parse_script(text)
    board = BoardParser.parse(board_text)

    for lines in command_blocks:
        _run_block(lines, board)


def _run_block(lines: list[str], board: Board) -> None:
    """Execute one command block's lines in order. Currently only
    `print board` (plus its embedded expected rows) is supported."""
    index = 0

    while index < len(lines):
        line = lines[index]

        if line == PRINT_BOARD_COMMAND:
            expected_rows = lines[index + 1: index + 1 + board.height]
            index += 1 + board.height
            _assert_board_matches(board, expected_rows)
            continue

        raise ValueError(f"unsupported command: {line!r}")


def _assert_board_matches(board: Board, expected_rows: list[str]) -> None:
    """Raise ScriptAssertionError if board's printed text doesn't match
    expected_rows exactly."""
    actual = BoardPrinter.to_text(board)
    expected = "\n".join(expected_rows)

    if actual != expected:
        raise ScriptAssertionError(f"print board mismatch:\nexpected:\n{expected}\nactual:\n{actual}")
