BOARD_MARKER = "Board:"
COMMANDS_MARKER = "Commands:"


def parse_sections(lines):
    """Splits raw fixture lines into (board_rows, command_lines)."""
    board_rows = []
    commands = []
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


def _cmd_print(args, session):
    if args == ["board"]:
        print(session.board.to_text())


def _cmd_click(args, session):
    if len(args) != 2:
        return

    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        return

    session.click(x, y)


def _cmd_wait(args, session):
    if len(args) != 1:
        return

    try:
        ms = int(args[0])
    except ValueError:
        return

    session.advance_clock(ms)


COMMAND_HANDLERS = {
    "print": _cmd_print,
    "click": _cmd_click,
    "wait": _cmd_wait,
}


def execute_commands(commands, session):
    for command in commands:
        tokens = command.split()
        if not tokens:
            continue

        handler = COMMAND_HANDLERS.get(tokens[0])
        if handler:
            handler(tokens[1:], session)
