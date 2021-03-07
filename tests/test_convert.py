import io
from contextlib import nullcontext as does_not_raise
from os.path import dirname, join, realpath
from typing import ContextManager

from pydantic.error_wrappers import ValidationError
from pytest import mark, raises

from repo_management import convert

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
            raises(ValueError),
        ),
        ("%FOO%\nbar\n", raises(ValidationError)),
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
            raises(ValidationError),
        ),
    ],
)
def test__desc_data_to_dict(
    file_data: str,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert convert._desc_data_to_model(data=io.StringIO(file_data))
