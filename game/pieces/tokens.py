VALID_PIECES = {"K", "Q", "R", "B", "N", "P"}
VALID_COLORS = {"w", "b"}

EMPTY_SQUARE = "."


def is_valid_token(token):
    if token == EMPTY_SQUARE:
        return True

    if len(token) != 2:
        return False

    return token[0] in VALID_COLORS and token[1] in VALID_PIECES
