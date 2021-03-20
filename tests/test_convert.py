import io
from contextlib import nullcontext as does_not_raise
from os.path import dirname, join, realpath
from typing import ContextManager

from pytest import mark, raises

from repo_management import convert, errors, models

RESOURCES = join(dirname(realpath(__file__)), "resources")


@mark.parametrize(
    "file_data, expectation",
    [
        ("%FILES%\nusr/\nusr/lib/\n", does_not_raise()),
        ("%FILES%usr/\nusr/lib/\n", raises(RuntimeError)),
        ("\n\n%FILES%usr/\nusr/lib/\n", raises(RuntimeError)),
        ("usr/\nusr/lib/\n", raises(RuntimeError)),
        ("usr/%FILES%\nusr/lib/\n", raises(RuntimeError)),
    ],
)
def test__files_data_to_dict(
    file_data: str,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert convert._files_data_to_model(data=io.StringIO(file_data))


@mark.parametrize(
    "file_data, expectation",
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
            does_not_raise(),
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
            raises(errors.RepoManagementValidationError),
        ),
        ("%FOO%\nbar\n", raises(errors.RepoManagementValidationError)),
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
            raises(errors.RepoManagementValidationError),
        ),
    ],
)
def test__desc_data_to_dict(
    file_data: str,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert convert._desc_data_to_model(data=io.StringIO(file_data))


@mark.parametrize(
    "desc, files",
    [
        (
            models.PackageDesc(
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
                sha256sum="foo",
                url="foo",
                version="foo",
            ),
            models.Files(files=["foo", "bar"]),
        ),
        (
            models.PackageDesc(
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
                sha256sum="foo",
                url="foo",
                version="foo",
            ),
            None,
        ),
    ],
)
def test__transform_package_desc_to_output_package(
    desc: models.PackageDesc,
    files: models.Files,
) -> None:
    output = convert._transform_package_desc_to_output_package(desc=desc, files=files)
    assert isinstance(output, models.OutputPackage)
    if files:
        assert output.files
    else:
        assert not output.files


def test_repodbfile__init() -> None:
    assert convert.RepoDbFile()


def test_repodbfile_render_desc_template() -> None:
    repodbfile = convert.RepoDbFile()
    assert repodbfile
    output = io.StringIO()
    assert not output.getvalue()
    repodbfile.render_desc_template(
        model=models.PackageDesc(
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
            sha256sum="foo",
            url="foo",
            version="foo",
        ),
        output=output,
    )
    assert output.getvalue()


def test_repodbfile_render_files_template() -> None:
    repodbfile = convert.RepoDbFile()
    assert repodbfile
    output = io.StringIO()
    assert not output.getvalue()
    repodbfile.render_files_template(
        model=models.Files(files=["foo", "bar"]),
        output=output,
    )
    assert output.getvalue()
