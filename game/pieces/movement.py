def _king_shape(d_row, d_col):
    return d_row <= 1 and d_col <= 1


def _rook_shape(d_row, d_col):
    return d_row == 0 or d_col == 0


def _bishop_shape(d_row, d_col):
    return d_row == d_col


def _queen_shape(d_row, d_col):
    return _rook_shape(d_row, d_col) or _bishop_shape(d_row, d_col)


def _knight_shape(d_row, d_col):
    return (d_row, d_col) in {(1, 2), (2, 1)}


def _pawn_shape(d_row, d_col):
    return True  # placeholder until pawn movement is implemented


MOVE_SHAPES = {
    "K": _king_shape,
    "R": _rook_shape,
    "B": _bishop_shape,
    "Q": _queen_shape,
    "N": _knight_shape,
    "P": _pawn_shape,
}


def is_legal_move(start, end, piece_type):
    if start == end:
        return False

    shape = MOVE_SHAPES.get(piece_type)
    if shape is None:
        return False

    d_row = abs(end[0] - start[0])
    d_col = abs(end[1] - start[1])

    return shape(d_row, d_col)
