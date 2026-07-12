import pytest

from texttests.script_parser import parse_script


def test_splits_board_text_from_command_blocks():
    text = "Board\n. . .\n. wK .\n\nprint board\n. . .\n. wK ."

    board_text, command_blocks = parse_script(text)

    assert board_text == ". . .\n. wK ."
    assert command_blocks == [["print board", ". . .", ". wK ."]]


def test_rejects_a_script_not_starting_with_board():
    with pytest.raises(ValueError):
        parse_script("print board\n. . .")
