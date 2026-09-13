import os
from pathlib import Path

FIXTURES = Path(__file__).with_name("fixtures")

def fixture_path(name: str) -> str:
    path = FIXTURES / name
    if not path.exists():
        raise FileNotFoundError(f"missing fixture: {path}")
    return str(path)
