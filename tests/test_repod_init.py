from pathlib import Path

import repod


def test_export_schemas(tmp_path: Path) -> None:
    repod.export_schemas(output=tmp_path)
