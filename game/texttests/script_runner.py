from engine.game_engine import GameEngine
from input.board_mapper import BoardMapper
from input.controller import Controller
from model.board import Board
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser
from text_io.board_printer import BoardPrinter
from texttests.script_parser import parse_script

PRINT_BOARD_COMMAND = "print board"
CLICK_COMMAND = "click"
WAIT_COMMAND = "wait"


class ScriptAssertionError(AssertionError):
    """Raised when a `print board` command's actual output does not match
    the expected rows embedded in the script."""


def run_script(text: str) -> None:
    """Executes a .kfc integration-test script by driving the same public
    command path a real user/UI would: BoardParser builds the board, then
    every click/wait/print board line is dispatched to a real
    Controller/GameEngine/RealTimeArbiter stack - never Board directly."""
    board_text, command_blocks = parse_script(text)
    board = BoardParser.parse(board_text)

    rule_engine = RuleEngine()
    real_time_arbiter = RealTimeArbiter(board)
    game_engine = GameEngine(board, rule_engine, real_time_arbiter)
    controller = Controller(board, BoardMapper(board), game_engine)

    for lines in command_blocks:
        _run_block(lines, board, controller, game_engine)


def _run_block(lines: list[str], board: Board, controller: Controller, game_engine: GameEngine) -> None:
    """Execute one command block's lines in order: click, wait, or
    print board (with its embedded expected rows)."""
    index = 0

    while index < len(lines):
        line = lines[index]
        tokens = line.split()

        if line == PRINT_BOARD_COMMAND:
            expected_rows = lines[index + 1: index + 1 + board.height]
            index += 1 + board.height
            _assert_board_matches(board, expected_rows)
            continue

        if tokens[0] == CLICK_COMMAND and len(tokens) == 3:
            controller.click(int(tokens[1]), int(tokens[2]))
            index += 1
            continue

        if tokens[0] == WAIT_COMMAND and len(tokens) == 2:
            game_engine.wait(int(tokens[1]))
            index += 1
            continue

        raise ValueError(f"unsupported command: {line!r}")


def _assert_board_matches(board: Board, expected_rows: list[str]) -> None:
    """Raise ScriptAssertionError if board's printed text doesn't match
    expected_rows exactly."""
    actual = BoardPrinter.to_text(board)
    expected = "\n".join(expected_rows)

    if actual != expected:
        raise ScriptAssertionError(f"print board mismatch:\nexpected:\n{expected}\nactual:\n{actual}")
