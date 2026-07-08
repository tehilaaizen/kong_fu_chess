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


def _print_board(board):
    print(board.to_text())


COMMAND_HANDLERS = {
    "print board": _print_board,
}


def execute_commands(commands, board):
    for command in commands:
        handler = COMMAND_HANDLERS.get(command)
        if handler:
            handler(board)
