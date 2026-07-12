class OccupiedCellError(Exception):
    """Raised when adding a piece to a cell that already holds one."""


class Board:
    """Board owns the logical arrangement of pieces, addressed by
    Position. It knows what exists on which cell, not which moves are
    legal - that decision belongs to the rules layer. Parsing text into a
    Board and printing a Board back to text are not Board's job either -
    see text_io/."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._pieces_by_cell = {}

    def in_bounds(self, position):
        return 0 <= position.row < self.height and 0 <= position.col < self.width

    def is_empty(self, position):
        return self.piece_at(position) is None

    def piece_at(self, position):
        return self._pieces_by_cell.get(position)

    def add_piece(self, piece):
        if not self.is_empty(piece.cell):
            raise OccupiedCellError(piece.cell)

        self._pieces_by_cell[piece.cell] = piece

    def remove_piece(self, position):
        self._pieces_by_cell.pop(position, None)

    def move_piece(self, source, destination):
        """Relocates the piece at source to destination. Assumes the move
        has already been validated - Board does not check chess legality."""
        piece = self._pieces_by_cell.pop(source)
        piece.cell = destination
        self._pieces_by_cell[destination] = piece
