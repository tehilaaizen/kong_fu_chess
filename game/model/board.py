from model.piece import Piece
from model.position import Position


class OccupiedCellError(Exception):
    """Raised when adding a piece to a cell that already holds one."""


class Board:
    """Board owns the logical arrangement of pieces, addressed by
    Position. It knows what exists on which cell, not which moves are
    legal - that decision belongs to the rules layer. Parsing text into a
    Board and printing a Board back to text are not Board's job either -
    see text_io/."""

    def __init__(self, width: int, height: int) -> None:
        """Create an empty board of the given size (no pieces placed)."""
        self.width = width
        self.height = height
        self._pieces_by_cell: dict[Position, Piece] = {}

    def in_bounds(self, position: Position) -> bool:
        """Whether position falls within this board's width/height."""
        return 0 <= position.row < self.height and 0 <= position.col < self.width

    def is_empty(self, position: Position) -> bool:
        """Whether no piece currently occupies position."""
        return self.piece_at(position) is None

    def piece_at(self, position: Position) -> Piece | None:
        """The piece occupying position, or None if it's empty."""
        return self._pieces_by_cell.get(position)

    def add_piece(self, piece: Piece) -> None:
        """Place piece at its own .cell. Raises OccupiedCellError if that
        cell is already taken."""
        if not self.is_empty(piece.cell):
            raise OccupiedCellError(piece.cell)

        self._pieces_by_cell[piece.cell] = piece

    def remove_piece(self, position: Position) -> None:
        """Clear position, if it holds a piece (a no-op otherwise)."""
        self._pieces_by_cell.pop(position, None)

    def move_piece(self, source: Position, destination: Position) -> None:
        """Relocates the piece at source to destination. Assumes the move
        has already been validated - Board does not check chess legality."""
        piece = self._pieces_by_cell.pop(source)
        piece.cell = destination
        self._pieces_by_cell[destination] = piece
