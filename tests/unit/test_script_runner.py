import pytest

from texttests.script_runner import ScriptAssertionError, run_script


def test_passes_when_printed_board_matches_expected_rows():
    run_script("Board\n. . .\n. wK .\n\nprint board\n. . .\n. wK .")


def test_raises_when_printed_board_does_not_match_expected_rows():
    with pytest.raises(ScriptAssertionError):
        run_script("Board\n. . .\n. wK .\n\nprint board\n. . .\n. . wK")


def test_raises_on_an_unsupported_command():
    with pytest.raises(ValueError):
        run_script("Board\n. . .\n. wK .\n\njump 50 50")
