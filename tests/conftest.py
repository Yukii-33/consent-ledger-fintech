"""Install declared project dependencies in bare pytest-only test environments."""

import importlib.util
import subprocess
import sys
from pathlib import Path


if importlib.util.find_spec("httpx") is None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-e", str(Path(__file__).resolve().parents[1])],
    )
