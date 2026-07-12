from pathlib import Path

import pytest

from texttests.script_runner import run_script

SCRIPTS_DIR = Path(__file__).parent / "scripts"
SCRIPT_PATHS = sorted(SCRIPTS_DIR.glob("*.kfc"))


@pytest.mark.parametrize("script_path", SCRIPT_PATHS, ids=lambda p: p.name)
def test_script(script_path):
    run_script(script_path.read_text())
