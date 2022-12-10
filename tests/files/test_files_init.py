"""Tests for repod.files."""
from pathlib import Path

from repod import files


def test_export_schemas(tmp_path: Path) -> None:
    """Tests for repod.files.export_schemas."""
    files.export_schemas(output=tmp_path)
