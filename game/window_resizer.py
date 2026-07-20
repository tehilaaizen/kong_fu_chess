from __future__ import annotations

from typing import Protocol

from view.geometry import BoardGeometry


class CellSized(Protocol):
    """Anything holding a mutable pixel cell size - BoardMapper satisfies
    this, letting the resizer retune click-to-cell mapping without
    depending on the concrete class."""

    cell_size: int


class ReloadableBoard(Protocol):
    """A board background source that can re-read itself at geometry's
    current size (BoardLoader)."""

    def reload(self) -> None:
        ...


class ReloadableAnimations(Protocol):
    """A sprite/clip source that can re-read every frame at a given cell
    size (AnimationLibrary)."""

    def reload(self, cell_size: int) -> None:
        ...


class WindowResizer:
    """Applies a new window size across every component whose pixels
    depend on it: rescales the shared BoardGeometry, retunes the mouse
    mapper's cell size, and re-reads the board background and all sprites
    at the new size. Renderers hold the same geometry instance and read
    it live each frame, so they need no notification - this is the whole
    set of things a resize must actively push to.

    Kept separate from GameWindow (which owns the untestable cv2 loop and
    the debounce that decides *when* to call this) so the actual resize
    effect is a plain, unit-testable method."""

    def __init__(
        self,
        geometry: BoardGeometry,
        board_mapper: CellSized,
        board_loader: ReloadableBoard,
        animation_library: ReloadableAnimations,
    ) -> None:
        self._geometry = geometry
        self._board_mapper = board_mapper
        self._board_loader = board_loader
        self._animation_library = animation_library

    def apply(self, outer_width_px: int, outer_height_px: int) -> None:
        """Rescale everything to a window of outer_width_px x
        outer_height_px: fit the geometry first (it computes the new cell
        size and centering margins), then push the new cell size to the
        mapper and reload the board and sprite assets to match."""
        self._geometry.fit_to_window(outer_width_px, outer_height_px)
        self._board_mapper.cell_size = self._geometry.cell_size_px
        self._board_loader.reload()
        self._animation_library.reload(self._geometry.cell_size_px)

    def current_window_size(self) -> tuple[int, int]:
        """Geometry's current outer (width, height) in pixels - the size
        GameWindow opens the window at and compares live window sizes
        against to detect a resize."""
        return self._geometry.window_width_px, self._geometry.window_height_px
