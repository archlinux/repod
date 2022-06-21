import io
from contextlib import nullcontext as does_not_raise
from os.path import dirname, join, realpath
from textwrap import dedent
from typing import ContextManager

from pytest import mark, raises

from repod import convert, errors
from repod.repo.package import Files, PackageDesc, RepoDbMemberTypeEnum
from repod.repo.package.syncdb import FilesV1, PackageDescV1
from tests.conftest import (
    FilesV9999,
    PackageDescV9999,
    create_base64_pgpsig,
    create_default_description,
    create_default_filename,
    create_default_full_version,
    create_default_packager,
    create_md5sum,
    create_sha256sum,
    create_url,
)

RESOURCES = join(dirname(realpath(__file__)), "resources")


@mark.parametrize(
    "file_data, data_type, expectation",
    [
        (
            f"""%ARCH%
            any

            %BACKUP%
            foo
            bar

            %BASE%
            foo

            %BUILDDATE%
            42

            %CONFLICTS%
            foo
            bar

            %CSIZE%
            23

            %DEPENDS%
            foo
            bar

            %DESC%
            foo

            %CHECKDEPENDS%
            foo
            bar

            %FILENAME%
            {create_default_filename()}

            %GROUPS%
            foo
            bar

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MAKEDEPENDS%
            foo
            bar

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            foo

            %OPTDEPENDS%
            foo
            bar

            %PACKAGER%
            {create_default_packager()}

            %PGPSIG%
            {create_base64_pgpsig()}

            %PROVIDES%
            foo
            bar

            %REPLACES%
            foo
            bar

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            {create_url()}

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            f"""%ARCH%
            any

            %BASE%
            foo

            %BUILDDATE%
            42

            %CSIZE%
            23

            %DESC%
            foo

            %FILENAME%
            {create_default_filename()}

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            foo

            %PACKAGER%
            {create_default_packager()}

            %PGPSIG%
            {create_base64_pgpsig()}

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            {create_url()}

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            f"""%ARCH%
            any

            %BASE%
            foo

            %BUILDDATE%
            42

            %CSIZE%
            23

            %DESC%
            foo

            %FILENAME%
            {create_default_filename()}

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            foo

            %PACKAGER%
            {create_default_packager()}

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            {create_url()}

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            f"""


            %ARCH%
            any

            %BACKUP%

            %BASE%
            foo

            %BUILDDATE%
            42

            %CONFLICTS%

            %CSIZE%
            23

            %DEPENDS%

            %DESC%
            foo

            %CHECKDEPENDS%

            %FILENAME%
            {create_default_filename()}

            %GROUPS%

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MAKEDEPENDS%

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            foo

            %OPTDEPENDS%

            %PACKAGER%
            {create_default_packager()}

            %PGPSIG%
            {create_base64_pgpsig()}

            %PROVIDES%

            %REPLACES%

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            {create_url()}

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            does_not_raise(),
        ),
        (
            f"""

            %ARCH%
            any

            %BACKUP%

            %BASE%
            foo

            %BUILDDATE%
            42

            %CONFLICTS%

            %CSIZE%
            23

            %DEPENDS%

            %DESC%
            foo

            %CHECKDEPENDS%

            %FILENAME%
            {create_default_filename()}

            %GROUPS%

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MAKEDEPENDS%

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            X-X-X

            %OPTDEPENDS%

            %PACKAGER%
            {create_default_packager()}

            %PGPSIG%
            {create_base64_pgpsig()}

            %PROVIDES%

            %REPLACES%

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            foo

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        (
            f"""
            %ARCH%
            any

            %BACKUP%

            %BASE%
            foo

            %BUILDDATE%
            42

            %CONFLICTS%

            %CSIZE%
            foo

            %DEPENDS%

            %DESC%
            foo

            %CHECKDEPENDS%

            %FILENAME%
            {create_default_filename()}

            %GROUPS%

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MAKEDEPENDS%

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            foo

            %OPTDEPENDS%

            %PACKAGER%
            {create_default_packager()}

            %PGPSIG%
            {create_base64_pgpsig()}

            %PROVIDES%

            %REPLACES%

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            {create_url()}

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        (
            """
            %FOO%
            bar
            """,
            RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        (
            f"""
            %BACKUP%

            %BASE%
            foo

            %BUILDDATE%
            42

            %CONFLICTS%

            %CSIZE%
            23

            %DEPENDS%

            %DESC%
            foo

            %CHECKDEPENDS%

            %FILENAME%
            {create_default_filename()}

            %GROUPS%

            %ISIZE%
            42

            %LICENSE%
            foo
            bar

            %MAKEDEPENDS%

            %MD5SUM%
            {create_md5sum()}

            %NAME%
            foo

            %OPTDEPENDS%

            %PACKAGER%
            {create_default_packager()}

            %PGPSIG%
            {create_base64_pgpsig()}

            %PROVIDES%

            %REPLACES%

            %SHA256SUM%
            {create_sha256sum()}

            %URL%
            {create_url()}

            %VERSION%
            1:1.0.0-1
            """,
            RepoDbMemberTypeEnum.DESC,
            raises(errors.RepoManagementValidationError),
        ),
        ("%FOO%\nbar\n", RepoDbMemberTypeEnum.UNKNOWN, raises(errors.RepoManagementFileError)),
        ("%FILES%\nfoo\n", RepoDbMemberTypeEnum.FILES, does_not_raise()),
        ("%FILES%\nhome/foo/bar\n", RepoDbMemberTypeEnum.FILES, raises(errors.RepoManagementValidationError)),
    ],
    ids=[
        "desc_v1, all fields populated",
        "desc_v1, minimum fields populated",
        "desc_v1, minimum fields populated, no pgpsig",
        "desc_v1, minimum fields populated, leading newline",
        "desc_v1, minimum fields populated, invalid name",
        "desc_v1, minimum fields populated, invalid csize",
        "desc_v1, single invalid field",
        "desc_v1, minimum fields populated, missing %ARCH% field",
        "unknown RepoDbMemberTypeEnum member",
        "files_v1",
        "files_v1, files in /home",
    ],
)
@mark.asyncio
async def test_file_data_to_model(
    file_data: str,
    data_type: RepoDbMemberTypeEnum,
    expectation: ContextManager[str],
) -> None:
    file_data = "\n".join([m.strip() for m in dedent(file_data).split("\n")])
    with expectation:
        assert await convert.file_data_to_model(
            data=io.StringIO(file_data),
            data_type=data_type,
            name="foo",
        )


def test_repodbfile__init() -> None:
    assert convert.RepoDbFile()


@mark.parametrize(
    "model, expectation",
    [
        (
            PackageDescV1(
                arch="any",
                base="foo",
                builddate=1,
                csize=1,
                desc=create_default_description(),
                filename=create_default_filename(),
                isize=1,
                license=["foo"],
                md5sum=create_md5sum(),
                name="foo",
                packager=create_default_packager(),
                pgpsig=create_base64_pgpsig(),
                sha256sum=create_sha256sum(),
                url="https://foobar.tld",
                version=create_default_full_version(),
            ),
            does_not_raise(),
        ),
        (
            PackageDescV1(
                arch="any",
                base="foo",
                builddate=1,
                csize=1,
                desc=create_default_description(),
                filename=create_default_filename(),
                isize=1,
                license=["foo"],
                md5sum=create_md5sum(),
                name="foo",
                packager=create_default_packager(),
                pgpsig=None,
                sha256sum=create_sha256sum(),
                url="https://foobar.tld",
                version=create_default_full_version(),
            ),
            does_not_raise(),
        ),
        (PackageDescV9999(), raises(errors.RepoManagementFileNotFoundError)),
    ],
)
@mark.asyncio
async def test_repodbfile_render_desc_template(model: PackageDesc, expectation: ContextManager[str]) -> None:
    repodbfile = convert.RepoDbFile()
    assert repodbfile
    output = io.StringIO()
    assert not output.getvalue()
    with expectation:
        await repodbfile.render_desc_template(
            model=model,
            output=output,
        )
        assert output.getvalue()


@mark.parametrize(
    "model, expectation",
    [
        (FilesV1(files=["foo", "bar"]), does_not_raise()),
        (FilesV9999(), raises(errors.RepoManagementFileNotFoundError)),
    ],
)
@mark.asyncio
async def test_repodbfile_render_files_template(model: Files, expectation: ContextManager[str]) -> None:
    repodbfile = convert.RepoDbFile()
    assert repodbfile
    output = io.StringIO()
    assert not output.getvalue()
    with expectation:
        await repodbfile.render_files_template(
            model=model,
            output=output,
        )
        assert output.getvalue()
