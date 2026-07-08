BOARD_MARKER = "Board:"
COMMANDS_MARKER = "Commands:"


def parse_sections(lines):
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
