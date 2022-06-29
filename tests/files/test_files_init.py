from pathlib import Path

from repod import files


def test_export_schemas(tmp_path: Path) -> None:
    files.export_schemas(output=tmp_path)
