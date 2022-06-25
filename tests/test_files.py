from pathlib import Path
from typing import Tuple

from pytest import mark

from repod import files
from repod.repo.package import RepoDbMemberData


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
