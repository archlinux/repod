import tarfile
from pathlib import Path
from typing import Tuple

from pytest import mark, raises

from repod import convert, errors, files
from repod.repo.management.outputpackage import OutputPackageBaseV1
from repod.repo.package import RepoDbMemberData, RepoDbTypeEnum


@mark.asyncio
async def test__read_db_file_member_as_model(files_sync_db_file: Tuple[Path, Path]) -> None:
    async for member in files._db_file_member_as_model(db_file=files.open_tarfile(files_sync_db_file[0])):
        assert isinstance(member, RepoDbMemberData)


@mark.parametrize(
    "member_name, result",
    [
        ("foo-bar-1.0.0-42", "foo-bar"),
        ("foobar-1.0.0-42", "foobar"),
        ("foo-bar-1.0.0-42/desc", "foo-bar"),
        ("foo-bar-1.0.0-42/files", "foo-bar"),
        ("foobar-1.0.0-42/desc", "foobar"),
        ("foobar-1.0.0-42/files", "foobar"),
    ],
)
@mark.asyncio
async def test__extract_db_member_package_name(
    member_name: str,
    result: str,
) -> None:
    assert await files._extract_db_member_package_name(name=member_name) == result


@mark.asyncio
async def test__json_files_in_directory(
    outputpackagebasev1_json_files_in_dir: Path,
    empty_dir: Path,
) -> None:
    async for json_file in files._json_files_in_directory(path=outputpackagebasev1_json_files_in_dir):
        assert isinstance(json_file, Path)

    with raises(errors.RepoManagementFileNotFoundError):
        async for json_file in files._json_files_in_directory(path=empty_dir):
            print(json_file)
            assert isinstance(json_file, Path)


@mark.asyncio
async def test__read_pkgbase_json_file(broken_json_file: Path, invalid_json_file: Path) -> None:
    with raises(errors.RepoManagementFileError):
        await files._read_pkgbase_json_file(path=broken_json_file)
    with raises(errors.RepoManagementValidationError):
        await files._read_pkgbase_json_file(path=invalid_json_file)


@mark.asyncio
async def test__write_db_file(empty_dir: Path) -> None:
    with files._write_db_file(empty_dir / "foo.db") as database:
        assert isinstance(database, tarfile.TarFile)


@mark.asyncio
async def test__stream_package_base_to_db(
    outputpackagebasev1: OutputPackageBaseV1,
    empty_file: Path,
) -> None:
    for db_type in [RepoDbTypeEnum.DEFAULT, RepoDbTypeEnum.FILES]:
        with files._write_db_file(path=empty_file) as database:
            await files._stream_package_base_to_db(
                db=database,
                model=outputpackagebasev1,
                repodbfile=convert.RepoDbFile(),
                db_type=db_type,
            )
