import io
from contextlib import nullcontext as does_not_raise
from os.path import dirname, join, realpath
from typing import ContextManager

from pytest import mark, raises

from repod import convert, errors, models

RESOURCES = join(dirname(realpath(__file__)), "resources")


@mark.parametrize(
    "file_data, data_type, expectation",
    [
        (
            (
                "%ARCH%\nfoo\n%BACKUP%\nfoo\nbar\n%BASE%\nfoo\n"
                "%BUILDDATE%\n42\n%CONFLICTS%\nfoo\nbar\n%CSIZE%\n23\n"
                "%DEPENDS%\nfoo\nbar\n%DESC%\nfoo\n%CHECKDEPENDS%\nfoo\nbar\n"
                "%FILENAME%\nfoo\n%GROUPS%\nfoo\nbar\n%ISIZE%\n42\n"
                "%LICENSE%\nfoo\nbar\n%MAKEDEPENDS%\nfoo\nbar\n%MD5SUM%\nfoo\n"
                "%NAME%\nfoo\n%OPTDEPENDS%\nfoo\nbar\n%PACKAGER%\nfoo\n"
                "%PGPSIG%\nfoo\n%PROVIDES%\nfoo\nbar\n%REPLACES%\nfoo\nbar\n"
                "%SHA256SUM%\nfoo\n%URL%\nfoo\n%VERSION%\nfoo\n"
            ),
            models.RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            (
                "%ARCH%\nfoo\n%BACKUP%\n%BASE%\nfoo\n"
                "%BUILDDATE%\n42\n%CONFLICTS%\n%CSIZE%\n23\n"
                "%DEPENDS%\n%DESC%\nfoo\n%CHECKDEPENDS%\n"
                "%FILENAME%\nfoo\n%GROUPS%\n%ISIZE%\n42\n"
                "%LICENSE%\nfoo\nbar\n%MAKEDEPENDS%\n%MD5SUM%\nfoo\n"
                "%NAME%\nfoo\n%OPTDEPENDS%\n%PACKAGER%\nfoo\n"
                "%PGPSIG%\nfoo\n%PROVIDES%\n%REPLACES%\n"
                "%SHA256SUM%\nfoo\n%URL%\nfoo\n%VERSION%\nfoo\n"
            ),
            models.RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            (
                "\n\n%ARCH%\nfoo\n%BACKUP%\nfoo\nbar\n%BASE%\nfoo\n"
                "%BUILDDATE%\n42\n%CONFLICTS%\nfoo\nbar\n%CSIZE%\n23\n"
                "%DEPENDS%\nfoo\nbar\n%DESC%\nfoo\n%CHECKDEPENDS%\nfoo\nbar\n"
                "%FILENAME%\nfoo\n%GROUPS%\nfoo\nbar\n%ISIZE%\n42\n"
                "%LICENSE%\nfoo\nbar\n%MAKEDEPENDS%\nfoo\nbar\n%MD5SUM%\nfoo\n"
                "%NAME%\nfoo\n%OPTDEPENDS%\nfoo\nbar\n%PACKAGER%\nfoo\n"
                "%PGPSIG%\nfoo\n%PROVIDES%\nfoo\nbar\n%REPLACES%\nfoo\nbar\n"
                "%SHA256SUM%\nfoo\n%URL%\nfoo\n%VERSION%\nfoo\n"
            ),
            models.RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            (
                "\n\n%ARCH%\nfoo\n%BACKUP%\nfoo\nbar\n%BASE%\nfoo\n"
                "%BUILDDATE%\n42\n%CONFLICTS%\nfoo\nbar\n%CSIZE%\n23\n"
                "%DEPENDS%\nfoo\nbar\n%DESC%\nfoo\n%CHECKDEPENDS%\nfoo\nbar\n"
                "%FILENAME%\nfoo\n%GROUPS%\nfoo\nbar\n%ISIZE%\n42\n"
                "%LICENSE%\nfoo\nbar\n%MAKEDEPENDS%\nfoo\nbar\n%MD5SUM%\nfoo\n"
                "%NAME%\nX-X-X\n%OPTDEPENDS%\nfoo\nbar\n%PACKAGER%\nfoo\n"
                "%PGPSIG%\nfoo\n%PROVIDES%\nfoo\nbar\n%REPLACES%\nfoo\nbar\n"
                "%SHA256SUM%\nfoo\n%URL%\nfoo\n%VERSION%\nfoo\n"
            ),
            models.RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        (
            (
                "%ARCH%\nfoo\n%BACKUP%\nfoo\nbar\n%BASE%\nfoo\n"
                "%BUILDDATE%\n42\n%CONFLICTS%\nfoo\nbar\n%CSIZE%\nfoo\n"
                "%DEPENDS%\nfoo\nbar\n%DESC%\nfoo\n%CHECKDEPENDS%\nfoo\nbar\n"
                "%FILENAME%\nfoo\n%GROUPS%\nfoo\nbar\n%ISIZE%\n42\n"
                "%LICENSE%\nfoo\nbar\n%MAKEDEPENDS%\nfoo\nbar\n%MD5SUM%\nfoo\n"
                "%NAME%\nfoo\n%OPTDEPENDS%\nfoo\nbar\n%PACKAGER%\nfoo\n"
                "%PGPSIG%\nfoo\n%PROVIDES%\nfoo\nbar\n%REPLACES%\nfoo\nbar\n"
                "%SHA256SUM%\nfoo\n%URL%\nfoo\n%VERSION%\nfoo\n"
            ),
            models.RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        ("%FOO%\nbar\n", models.RepoDbMemberTypeEnum.DESC, raises(errors.RepoManagementValidationError)),
        (
            (
                "%BACKUP%\nfoo\nbar\n%BASE%\nfoo\n"
                "%BUILDDATE%\n42\n%CONFLICTS%\nfoo\nbar\n%CSIZE%\n23\n"
                "%DEPENDS%\nfoo\nbar\n%DESC%\nfoo\n%CHECKDEPENDS%\nfoo\nbar\n"
                "%FILENAME%\nfoo\n%GROUPS%\nfoo\nbar\n%ISIZE%\n42\n"
                "%LICENSE%\nfoo\nbar\n%MAKEDEPENDS%\nfoo\nbar\n%MD5SUM%\nfoo\n"
                "%NAME%\nfoo\n%OPTDEPENDS%\nfoo\nbar\n%PACKAGER%\nfoo\n"
                "%PGPSIG%\nfoo\n%PROVIDES%\nfoo\nbar\n%REPLACES%\nfoo\nbar\n"
                "%SHA256SUM%\nfoo\n%URL%\nfoo\n%VERSION%\nfoo\n"
            ),
            models.RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        ("%FOO%\nbar\n", models.RepoDbMemberTypeEnum.UNKNOWN, raises(errors.RepoManagementFileError)),
        ("%FILES%\nfoo\n", models.RepoDbMemberTypeEnum.FILES, does_not_raise()),
        ("%FILES%\nhome/foo/bar\n", models.RepoDbMemberTypeEnum.FILES, raises(errors.RepoManagementValidationError)),
    ],
)
@mark.asyncio
async def test_file_data_to_model(
    file_data: str,
    data_type: models.RepoDbMemberTypeEnum,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert await convert.file_data_to_model(
            data=io.StringIO(file_data),
            data_type=data_type,
            name="foo",
        )


def test_repodbfile__init() -> None:
    assert convert.RepoDbFile()


@mark.parametrize(
    "schema_version, expectation",
    [
        (1, does_not_raise()),
        (9999, raises(errors.RepoManagementFileNotFoundError)),
    ],
)
@mark.asyncio
async def test_repodbfile_render_desc_template(schema_version: int, expectation: ContextManager[str]) -> None:
    repodbfile = convert.RepoDbFile()
    assert repodbfile
    output = io.StringIO()
    assert not output.getvalue()
    with expectation:
        await repodbfile.render_desc_template(
            model=models.package.PackageDescV1(
                arch="foo",
                base="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                packager="foo",
                pgpsig="foo",
                schema_version=schema_version,
                sha256sum="foo",
                url="foo",
                version="foo",
            ),
            output=output,
        )
        assert output.getvalue()


@mark.parametrize(
    "schema_version, expectation",
    [
        (1, does_not_raise()),
        (9999, raises(errors.RepoManagementFileNotFoundError)),
    ],
)
@mark.asyncio
async def test_repodbfile_render_files_template(schema_version: int, expectation: ContextManager[str]) -> None:
    repodbfile = convert.RepoDbFile()
    assert repodbfile
    output = io.StringIO()
    assert not output.getvalue()
    with expectation:
        await repodbfile.render_files_template(
            model=models.package.FilesV1(files=["foo", "bar"], schema_version=schema_version),
            output=output,
        )
        assert output.getvalue()
