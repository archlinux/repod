from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, ContextManager, Dict, List, Optional, Set, Union
from unittest.mock import patch

from pytest import mark, raises

from repod.errors import RepoManagementFileError, RepoManagementValidationError
from repod.repo.management import OutputPackage, OutputPackageBase
from repod.repo.package import syncdb
from tests.conftest import (
    PackageDescV9999,
    create_base64_pgpsig,
    create_default_filename,
    create_default_full_version,
    create_default_packager,
    create_md5sum,
    create_sha256sum,
    create_url,
)


def test_get_desc_json_name() -> None:

    for identifier in syncdb.DESC_JSON.keys():
        with does_not_raise():
            assert syncdb.get_desc_json_name(key=identifier) == syncdb.DESC_JSON[identifier][0]

    with raises(RepoManagementFileError):
        syncdb.get_desc_json_name(key="%FOO%")


def test_get_desc_json_field_type() -> None:

    for identifier in syncdb.DESC_JSON.keys():
        with does_not_raise():
            assert syncdb.get_desc_json_field_type(key=identifier) == syncdb.DESC_JSON[identifier][1]

    with raises(RepoManagementFileError):
        syncdb.get_desc_json_field_type(key="%FOO%")


def test_get_files_json_name() -> None:

    for identifier in syncdb.FILES_JSON.keys():
        with does_not_raise():
            assert syncdb.get_files_json_name(key=identifier) == syncdb.FILES_JSON[identifier][0]

    with raises(RepoManagementFileError):
        syncdb.get_files_json_name(key="%FOO%")


def test_get_files_json_field_type() -> None:

    for identifier in syncdb.FILES_JSON.keys():
        with does_not_raise():
            assert syncdb.get_files_json_field_type(key=identifier) == syncdb.FILES_JSON[identifier][1]

    with raises(RepoManagementFileError):
        syncdb.get_files_json_field_type(key="%FOO%")


def test_files_get_schema_version() -> None:
    model = syncdb.Files()
    with raises(RuntimeError):
        model.get_schema_version()


@mark.parametrize(
    "data, expectation",
    [
        (
            {"files": ["foo", "bar"]},
            does_not_raise(),
        ),
        (
            {"files": ["foo", "bar"], "schema_version": 9999},
            raises(RepoManagementValidationError),
        ),
        (
            {"files": "foo"},
            raises(RepoManagementValidationError),
        ),
        (
            {"foo": "bar"},
            raises(RepoManagementValidationError),
        ),
    ],
)
def test_files_from_dict(data: Dict[str, Any], expectation: ContextManager[str]) -> None:
    with expectation:
        syncdb.Files.from_dict(data=data)


@mark.parametrize(
    "files_versions, default_files_version, files_dict, emit_warning, expectation",
    [
        (
            {1: {"required": {"files"}, "optional": {"foo"}}, 2: {"required": {"files"}, "optional": set()}},
            2,
            {"files": ["foo", "bar"], "foo": ["bar"]},
            True,
            does_not_raise(),
        ),
        (
            {1: {"required": {"files"}, "optional": {"foo"}}},
            1,
            {"files": ["foo", "bar"], "bar": ["baz"]},
            False,
            raises(RepoManagementValidationError),
        ),
        (
            {1: {"required": {"files"}, "optional": {"foo", "bar"}}},
            1,
            {"files": ["foo", "bar"], "foo": ["bar"]},
            False,
            does_not_raise(),
        ),
    ],
)
def test_files_from_dict_derive_file_version(
    files_versions: Dict[int, Dict[str, Set[str]]],
    default_files_version: int,
    files_dict: Dict[str, List[str]],
    emit_warning: bool,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        with patch("logging.warning") as logging_warning_mock:
            with patch("repod.repo.package.syncdb.FILES_VERSIONS", files_versions):
                with patch("repod.repo.package.syncdb.DEFAULT_FILES_VERSION", default_files_version):
                    syncdb.Files.from_dict(data=files_dict)
                    if emit_warning:
                        logging_warning_mock.assert_called_once()


@mark.parametrize(
    "files_versions, default_version, input_dict, emit_warning, expectation",
    [
        (
            {
                1: {
                    "required": {
                        "arch",
                        "base",
                        "builddate",
                        "csize",
                        "desc",
                        "filename",
                        "isize",
                        "license",
                        "md5sum",
                        "name",
                        "packager",
                        "pgpsig",
                        "sha256sum",
                        "url",
                        "version",
                    },
                    "optional": {
                        "checkdepends",
                        "conflicts",
                        "depends",
                        "backup",
                        "groups",
                        "makedepends",
                        "optdepends",
                        "provides",
                        "replaces",
                    },
                    "output_package_version": 1,
                    "output_package_base_version": 1,
                },
                2: {
                    "required": {
                        "arch",
                        "base",
                        "builddate",
                        "csize",
                        "desc",
                        "isize",
                        "license",
                        "md5sum",
                        "name",
                        "packager",
                        "pgpsig",
                        "sha256sum",
                        "url",
                        "version",
                    },
                    "optional": {},
                    "output_package_version": 2,
                    "output_package_base_version": 2,
                },
            },
            2,
            {
                "arch": "any",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": create_default_filename(),
                "isize": 1,
                "license": ["foo"],
                "md5sum": create_md5sum(),
                "name": "foo",
                "packager": create_default_packager(),
                "pgpsig": create_base64_pgpsig(),
                "sha256sum": create_sha256sum(),
                "url": create_url(),
                "version": create_default_full_version(),
            },
            True,
            does_not_raise(),
        ),
        (
            {
                1: {
                    "required": {
                        "arch",
                        "base",
                        "builddate",
                        "csize",
                        "desc",
                        "filename",
                        "isize",
                        "license",
                        "md5sum",
                        "name",
                        "packager",
                        "sha256sum",
                        "url",
                        "version",
                    },
                    "optional": {
                        "checkdepends",
                        "conflicts",
                        "depends",
                        "backup",
                        "groups",
                        "makedepends",
                        "optdepends",
                        "pgpsig",
                        "provides",
                        "replaces",
                    },
                    "output_package_version": 1,
                    "output_package_base_version": 1,
                },
            },
            1,
            {
                "arch": "any",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": create_default_filename(),
                "isize": 1,
                "license": ["foo"],
                "md5sum": create_md5sum(),
                "name": "foo",
                "packager": create_default_packager(),
                "pgpsig": None,
                "sha256sum": create_sha256sum(),
                "url": create_url(),
                "version": create_default_full_version(),
            },
            False,
            does_not_raise(),
        ),
    ],
    ids=[
        "default version 2 does not match",
        "default version 1 matches, no pgpsig",
    ],
)
def test_package_desc_from_dict_derive_file_version(
    files_versions: Dict[int, Dict[str, Set[str]]],
    default_version: int,
    input_dict: Dict[str, Union[int, str, List[str]]],
    emit_warning: bool,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        with patch("logging.warning") as logging_warning_mock:
            with patch("repod.repo.package.syncdb.PACKAGE_DESC_VERSIONS", files_versions):
                with patch("repod.repo.package.syncdb.DEFAULT_PACKAGE_DESC_VERSION", default_version):
                    syncdb.PackageDesc.from_dict(data=input_dict)
                    if emit_warning:
                        logging_warning_mock.assert_called_once()


@mark.parametrize(
    "no_files, invalid_packagedesc_version, expectation",
    [
        (False, False, does_not_raise()),
        (True, False, does_not_raise()),
        (True, True, raises(RepoManagementValidationError)),
    ],
)
def test_package_desc_v1_get_output_package_v1(
    outputpackagev1: OutputPackage,
    packagedescv1: syncdb.PackageDesc,
    filesv1: Optional[syncdb.FilesV1],
    no_files: bool,
    invalid_packagedesc_version: bool,
    expectation: ContextManager[str],
) -> None:
    output_package = outputpackagev1
    package_desc = packagedescv1
    files = filesv1
    if no_files:
        output_package.files = None  # type: ignore[attr-defined]
        files = None
    if invalid_packagedesc_version:
        package_desc = PackageDescV9999()

    with expectation:
        assert output_package == package_desc.get_output_package(files)


def test_package_desc_get_output_package_inconsistent_schema_config(packagedescv1: syncdb.PackageDesc) -> None:
    with patch("repod.repo.package.syncdb.PACKAGE_DESC_VERSIONS", {1: {"output_package_version": 9999}}):
        with raises(RuntimeError):
            packagedescv1.get_output_package(files=None)


@mark.parametrize(
    "no_files, invalid_package_desc, expectation",
    [
        (False, False, does_not_raise()),
        (True, False, does_not_raise()),
        (False, True, raises(RepoManagementValidationError)),
        (True, True, raises(RepoManagementValidationError)),
    ],
)
def test_package_desc_v1_get_output_package_base_v1(
    outputpackagebasev1: OutputPackageBase,
    packagedescv1: syncdb.PackageDesc,
    filesv1: Optional[syncdb.Files],
    no_files: bool,
    invalid_package_desc: bool,
    expectation: ContextManager[str],
) -> None:
    output_package_base = outputpackagebasev1
    package_desc = packagedescv1
    files = filesv1
    # remove all but the first package
    output_package_base.packages = output_package_base.packages[0:1]  # type: ignore[attr-defined]

    if no_files:
        files = None
        output_package_base.packages[0].files = None  # type: ignore[attr-defined]
    if invalid_package_desc:
        package_desc = PackageDescV9999()

    with expectation:
        assert output_package_base == package_desc.get_output_package_base(files)


def test_package_desc_get_output_package_base_inconsistent_schema_config(
    packagedescv1: syncdb.PackageDesc,
) -> None:
    with patch("repod.repo.package.syncdb.PACKAGE_DESC_VERSIONS", {1: {"output_package_base_version": 9999}}):
        with raises(RuntimeError):
            packagedescv1.get_output_package_base(files=None)


def test_packagedesc_get_base() -> None:
    model = syncdb.PackageDesc()
    with raises(RuntimeError):
        model.get_base()


def test_packagedesc_get_name() -> None:
    model = syncdb.PackageDesc()
    with raises(RuntimeError):
        model.get_name()


def test_packagedesc_get_schema_version() -> None:
    model = syncdb.PackageDesc()
    with raises(RuntimeError):
        model.get_schema_version()


def test_packagedesc_get_output_package() -> None:
    files = syncdb.FilesV1(files=["foo", "bar", "baz"])
    model = syncdb.PackageDesc()
    with raises(RuntimeError):
        model.get_output_package(files=files)


def test_packagedesc_get_output_package_base() -> None:
    files = syncdb.FilesV1(files=["foo", "bar", "baz"])
    model = syncdb.PackageDesc()
    with raises(RuntimeError):
        model.get_output_package_base(files=files)


@mark.parametrize(
    "data, expectation",
    [
        (
            {
                "arch": "any",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": create_default_filename(),
                "isize": 1,
                "license": ["foo"],
                "md5sum": create_md5sum(),
                "name": "foo",
                "packager": create_default_packager(),
                "pgpsig": create_base64_pgpsig(),
                "sha256sum": create_sha256sum(),
                "url": create_url(),
                "version": create_default_full_version(),
            },
            does_not_raise(),
        ),
        (
            {
                "arch": "any",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": create_default_filename(),
                "isize": 1,
                "license": ["foo"],
                "md5sum": create_md5sum(),
                "name": "foo",
                "packager": create_default_packager(),
                "pgpsig": create_base64_pgpsig(),
                "sha256sum": create_sha256sum(),
                "url": create_url(),
            },
            raises(RepoManagementValidationError),
        ),
        (
            {
                "arch": "any",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": create_default_filename(),
                "isize": 1,
                "license": ["foo"],
                "md5sum": create_md5sum(),
                "name": "foo",
                "packager": create_default_packager(),
                "pgpsig": create_base64_pgpsig(),
                "sha256sum": create_sha256sum(),
                "url": create_url(),
                "version": create_default_full_version(),
                "foo": "bar",
            },
            raises(RepoManagementValidationError),
        ),
    ],
    ids=[
        "default",
        "version missing",
        "invalid key-value pair",
    ],
)
def test_packagedesc_from_dict(data: Dict[str, Union[int, str, List[str]]], expectation: ContextManager[str]) -> None:
    with expectation:
        syncdb.PackageDesc.from_dict(data=data)


def test_export_schemas(tmp_path: Path) -> None:
    syncdb.export_schemas(output=str(tmp_path))
    syncdb.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        syncdb.export_schemas(output="/foobar")

    with raises(RuntimeError):
        syncdb.export_schemas(output=Path("/foobar"))
