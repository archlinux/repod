from pathlib import Path

from repod import repo


def test_export_schemas(tmp_path: Path) -> None:
    repo.export_schemas(output=tmp_path)
