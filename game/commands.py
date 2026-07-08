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
