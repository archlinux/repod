"""Tests for repod."""
from pathlib import Path

import repod


def test_export_schemas(tmp_path: Path) -> None:
    """Tests for repod.export_schemas."""
    repod.export_schemas(output=tmp_path)
