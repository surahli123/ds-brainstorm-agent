"""Add autoresearch/ to sys.path so tests can import loop_runner and evaluate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "autoresearch"))
