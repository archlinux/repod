from logging import DEBUG
from pathlib import Path
from typing import Tuple

from pytest import LogCaptureFixture, raises

from repod.errors import RepoManagementFileError
from repod.files import package


async def test_package_from_file(
    caplog: LogCaptureFixture,
    default_package_file: Path,
    default_sync_db_file: Tuple[Path],
) -> None:
    caplog.set_level(DEBUG)
    assert isinstance(await package.Package.from_file(path=default_package_file), package.PackageV1)

    with raises(RepoManagementFileError):
        await package.Package.from_file(path=default_sync_db_file[0])


def test_export_schemas(tmp_path: Path) -> None:
    package.export_schemas(output=str(tmp_path))
    package.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        package.export_schemas(output="/foobar")

    with raises(RuntimeError):
        package.export_schemas(output=Path("/foobar"))
