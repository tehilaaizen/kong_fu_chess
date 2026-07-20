from input.board_mapper import BoardMapper
from model.board import Board
from model.position import Position


def _mapper():
    return BoardMapper(Board(width=3, height=3))


def test_maps_low_pixel_range_to_column_zero():
    assert _mapper().pixel_to_cell(50, 50) == Position(0, 0)


def test_maps_next_pixel_range_to_column_one():
    assert _mapper().pixel_to_cell(150, 50) == Position(0, 1)


def test_maps_next_pixel_range_to_row_one():
    assert _mapper().pixel_to_cell(50, 150) == Position(1, 0)


def test_click_outside_the_board_returns_none():
    assert _mapper().pixel_to_cell(1000, 1000) is None


def test_cell_size_can_be_retuned_for_a_resize():
    mapper = BoardMapper(Board(width=3, height=3), cell_size=50)
    assert mapper.pixel_to_cell(60, 10) == Position(0, 1)  # 60 // 50 == 1

    mapper.cell_size = 100

    assert mapper.pixel_to_cell(60, 10) == Position(0, 0)  # 60 // 100 == 0
