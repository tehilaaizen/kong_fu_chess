BOARD_KEYWORD = "Board"


def parse_script(text):
    """Splits a .kfc script into the board-notation text and the list of
    command blocks that follow it (blank lines separate blocks)."""
    blocks = _split_into_blocks(text)

    if not blocks or blocks[0][0] != BOARD_KEYWORD:
        raise ValueError("script must start with a 'Board' block")

    board_text = "\n".join(blocks[0][1:])
    command_blocks = blocks[1:]

    return board_text, command_blocks


def _split_into_blocks(text):
    blocks = []
    current = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            if current:
                blocks.append(current)
                current = []
            continue

        current.append(line)

    if current:
        blocks.append(current)

    return blocks
