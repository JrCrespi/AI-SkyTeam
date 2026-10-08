"""Location of the bundled data files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
