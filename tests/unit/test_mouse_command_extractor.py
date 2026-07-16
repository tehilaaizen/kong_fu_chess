from input.commands import ClickCommand, JumpCommand
from input.mouse_command_extractor import MouseCommandExtractor
from view.geometry import BoardGeometry


def _geometry_with_no_offset() -> BoardGeometry:
    return BoardGeometry(left_column_width_px=0, right_column_width_px=0)


def test_extract_left_click_inside_the_board_returns_a_click_command():
    extractor = MouseCommandExtractor(_geometry_with_no_offset())

    command = extractor.extract_left_click(150, 250)

    assert command == ClickCommand(150, 250)


def test_extract_right_click_inside_the_board_returns_a_jump_command():
    extractor = MouseCommandExtractor(_geometry_with_no_offset())

    command = extractor.extract_right_click(150, 250)

    assert command == JumpCommand(150, 250)


def test_extract_left_click_outside_the_board_returns_none():
    extractor = MouseCommandExtractor(_geometry_with_no_offset())

    command = extractor.extract_left_click(9999, 9999)

    assert command is None


def test_extract_left_click_with_negative_coordinates_returns_none():
    extractor = MouseCommandExtractor(_geometry_with_no_offset())

    command = extractor.extract_left_click(-5, 10)

    assert command is None


def test_extractor_subtracts_the_geometrys_origin_offset():
    geometry = BoardGeometry(left_column_width_px=100, board_origin_y=50)
    extractor = MouseCommandExtractor(geometry)

    command = extractor.extract_left_click(150, 100)

    assert command == ClickCommand(50, 50)


def test_a_click_before_the_origin_offset_is_outside_the_board():
    geometry = BoardGeometry(left_column_width_px=100, board_origin_y=50)
    extractor = MouseCommandExtractor(geometry)

    command = extractor.extract_left_click(50, 50)

    assert command is None


def test_a_click_in_the_default_left_hud_column_is_outside_the_board():
    extractor = MouseCommandExtractor(BoardGeometry())

    command = extractor.extract_left_click(50, 50)

    assert command is None
