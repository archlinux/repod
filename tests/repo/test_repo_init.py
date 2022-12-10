"""Tests for repod.repo."""
from pathlib import Path

from repod import repo


def test_export_schemas(tmp_path: Path) -> None:
    """Tests for repod.repo.export_schemas."""
    repo.export_schemas(output=tmp_path)
