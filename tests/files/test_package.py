from contextlib import nullcontext as does_not_raise
from logging import DEBUG
from pathlib import Path
from typing import ContextManager, Tuple

from pytest import LogCaptureFixture, mark, raises

from repod.errors import RepoManagementFileError
from repod.files import package


@mark.parametrize(
    "add_sig, valid_sig_name, sig_exists, expectation",
    [
        (True, True, True, does_not_raise()),
        (True, False, True, raises(RepoManagementFileError)),
        (True, True, False, raises(RepoManagementFileError)),
        (False, True, True, does_not_raise()),
    ],
)
async def test_package_from_file(
    add_sig: bool,
    valid_sig_name: bool,
    sig_exists: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    default_sync_db_file: Tuple[Path],
) -> None:
    caplog.set_level(DEBUG)

    signature = default_package_file[1]

    if not sig_exists:
        signature.unlink()

    if not valid_sig_name:
        signature = Path("foo")

    with expectation:
        assert isinstance(
            await package.Package.from_file(
                package=default_package_file[0],
                signature=signature if add_sig else None,
            ),
            package.PackageV1,
        )

    with raises(RepoManagementFileError):
        await package.Package.from_file(package=default_sync_db_file[0])


async def test_packagev1_top_level_dict(
    caplog: LogCaptureFixture,
    packagev1: package.PackageV1,
) -> None:
    caplog.set_level(DEBUG)
    keys = set(packagev1.top_level_dict().keys())
    assert len(packagev1.buildinfo.dict().keys() - keys) == 0
    assert len(packagev1.mtree.dict().keys() - keys) == 0
    assert len(packagev1.pkginfo.dict().keys() - keys) == 0
    assert len({"csize", "filename", "md5sum", "pgpsig", "sha256sum"} - keys) == 0


def test_export_schemas(tmp_path: Path) -> None:
    package.export_schemas(output=str(tmp_path))
    package.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        package.export_schemas(output="/foobar")

    with raises(RuntimeError):
        package.export_schemas(output=Path("/foobar"))
