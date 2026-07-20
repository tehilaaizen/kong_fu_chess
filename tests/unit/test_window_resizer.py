from view.geometry import BoardGeometry
from window_resizer import WindowResizer


class _FakeMapper:
    def __init__(self) -> None:
        self.cell_size = 100


class _FakeBoardLoader:
    def __init__(self) -> None:
        self.reload_count = 0

    def reload(self) -> None:
        self.reload_count += 1


class _FakeAnimationLibrary:
    def __init__(self) -> None:
        self.reloaded_cell_sizes: list[int] = []

    def reload(self, cell_size: int) -> None:
        self.reloaded_cell_sizes.append(cell_size)


def _resizer():
    geometry = BoardGeometry()
    mapper = _FakeMapper()
    board_loader = _FakeBoardLoader()
    animation_library = _FakeAnimationLibrary()
    return WindowResizer(geometry, mapper, board_loader, animation_library), geometry, mapper, board_loader, animation_library


def test_apply_rescales_geometry():
    resizer, geometry, _, _, _ = _resizer()

    resizer.apply(2400, 1600)

    assert geometry.cell_size_px == 200
    assert (geometry.window_width_px, geometry.window_height_px) == (2400, 1600)


def test_apply_pushes_the_new_cell_size_to_the_mapper():
    resizer, geometry, mapper, _, _ = _resizer()

    resizer.apply(2400, 1600)

    assert mapper.cell_size == geometry.cell_size_px == 200


def test_apply_reloads_the_board_and_the_sprites_at_the_new_cell_size():
    resizer, _, _, board_loader, animation_library = _resizer()

    resizer.apply(2400, 1600)

    assert board_loader.reload_count == 1
    assert animation_library.reloaded_cell_sizes == [200]


def test_current_window_size_reports_geometrys_outer_size():
    resizer, _, _, _, _ = _resizer()

    assert resizer.current_window_size() == (1200, 800)
    resizer.apply(2400, 1600)
    assert resizer.current_window_size() == (2400, 1600)
