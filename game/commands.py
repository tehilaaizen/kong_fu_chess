from engine.game_engine import GameEngine
from input.controller import Controller
from model.board import Board
from text_io.board_printer import BoardPrinter

BOARD_MARKER = "Board:"
COMMANDS_MARKER = "Commands:"


class CommandContext:
    """Bundles the collaborators command handlers need, so
    COMMAND_HANDLERS can share one dispatch signature without a god
    object holding game logic itself."""

    def __init__(self, board: Board, controller: Controller, game_engine: GameEngine) -> None:
        self.board = board
        self.controller = controller
        self.game_engine = game_engine


def parse_sections(lines: list[str]) -> tuple[str, list[str]]:
    """Splits raw fixture lines into (board_text, command_lines)."""
    board_lines: list[str] = []
    commands: list[str] = []
    in_board = False

    for line in lines:
        if line == BOARD_MARKER:
            in_board = True
            continue

        if line == COMMANDS_MARKER:
            in_board = False
            continue

        if not line:
            continue

        if in_board:
            board_lines.append(line)
        else:
            commands.append(line)

    return "\n".join(board_lines), commands


def _cmd_print(args: list[str], context: CommandContext) -> None:
    if args == ["board"]:
        print(BoardPrinter.to_text(context.board))


def _cmd_click(args: list[str], context: CommandContext) -> None:
    if len(args) != 2:
        return

    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        return

    context.controller.click(x, y)


def _cmd_wait(args: list[str], context: CommandContext) -> None:
    if len(args) != 1:
        return

    try:
        ms = int(args[0])
    except ValueError:
        return

    context.game_engine.wait(ms)


def _cmd_jump(args: list[str], context: CommandContext) -> None:
    if len(args) != 2:
        return

    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        return

    context.controller.jump(x, y)


COMMAND_HANDLERS = {
    "print": _cmd_print,
    "click": _cmd_click,
    "wait": _cmd_wait,
    "jump": _cmd_jump,
}


def execute_commands(commands: list[str], context: CommandContext) -> None:
    """Run each command line against context, in order, dispatching
    through COMMAND_HANDLERS by its first token."""
    for command in commands:
        tokens = command.split()
        if not tokens:
            continue

        handler = COMMAND_HANDLERS.get(tokens[0])
        if handler:
            handler(tokens[1:], context)
