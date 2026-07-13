from session import GameSession

BOARD_MARKER = "Board:"
COMMANDS_MARKER = "Commands:"


def parse_sections(lines: list[str]) -> tuple[list[list[str]], list[str]]:
    """Splits raw fixture lines into (board_rows, command_lines)."""
    board_rows: list[list[str]] = []
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
            board_rows.append(line.split())
        else:
            commands.append(line)

    return board_rows, commands


def _cmd_print(args: list[str], session: GameSession) -> None:
    """Handle `print board`: print the session's board as text."""
    if args == ["board"]:
        print(session.board.to_text())


def _cmd_click(args: list[str], session: GameSession) -> None:
    """Handle `click <x> <y>`: forward the pixel coordinates to the session."""
    if len(args) != 2:
        return

    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        return

    session.click(x, y)


def _cmd_wait(args: list[str], session: GameSession) -> None:
    """Handle `wait <ms>`: advance the session's simulated clock."""
    if len(args) != 1:
        return

    try:
        ms = int(args[0])
    except ValueError:
        return

    session.advance_clock(ms)


def _cmd_jump(args: list[str], session: GameSession) -> None:
    """Handle `jump <x> <y>`: forward the pixel coordinates to the session."""
    if len(args) != 2:
        return

    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        return

    session.jump(x, y)


COMMAND_HANDLERS = {
    "print": _cmd_print,
    "click": _cmd_click,
    "wait": _cmd_wait,
    "jump": _cmd_jump,
}


def execute_commands(commands: list[str], session: GameSession) -> None:
    """Run each command line against session, in order, dispatching
    through COMMAND_HANDLERS by its first token."""
    for command in commands:
        tokens = command.split()
        if not tokens:
            continue

        handler = COMMAND_HANDLERS.get(tokens[0])
        if handler:
            handler(tokens[1:], session)
