from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, ContextManager, Dict, List, Optional, Set, Union
from unittest.mock import patch

from pydantic import ValidationError
from pytest import mark, raises

from repod import errors, models
from repod.common import models as common_models
from repod.models.repo import DESC_JSON, FILES_JSON
from tests.conftest import (
    OutputPackageBaseV9999,
    PackageDescV9999,
    create_base64_pgpsig,
    create_default_filename,
    create_default_full_version,
    create_default_packager,
    create_md5sum,
    create_sha256sum,
    create_url,
)


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
            with patch("repod.models.package.PACKAGE_DESC_VERSIONS", files_versions):
                with patch("repod.models.package.DEFAULT_PACKAGE_DESC_VERSION", default_version):
                    models.PackageDesc.from_dict(data=input_dict)
                    if emit_warning:
                        logging_warning_mock.assert_called_once()


@mark.parametrize(
    "no_files, invalid_packagedesc_version, expectation",
    [
        (False, False, does_not_raise()),
        (True, False, does_not_raise()),
        (True, True, raises(errors.RepoManagementValidationError)),
    ],
)
def test_package_desc_v1_get_output_package_v1(
    outputpackagev1: models.OutputPackage,
    packagedescv1: models.PackageDesc,
    filesv1: Optional[models.package.FilesV1],
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


def test_package_desc_get_output_package_inconsistent_schema_config(packagedescv1: models.PackageDesc) -> None:
    with patch("repod.models.package.PACKAGE_DESC_VERSIONS", {1: {"output_package_version": 9999}}):
        with raises(RuntimeError):
            packagedescv1.get_output_package(files=None)


@mark.parametrize(
    "no_files, invalid_package_desc, expectation",
    [
        (False, False, does_not_raise()),
        (True, False, does_not_raise()),
        (False, True, raises(errors.RepoManagementValidationError)),
        (True, True, raises(errors.RepoManagementValidationError)),
    ],
)
def test_package_desc_v1_get_output_package_base_v1(
    outputpackagebasev1: models.OutputPackageBase,
    packagedescv1: models.PackageDesc,
    filesv1: Optional[models.Files],
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
    packagedescv1: models.PackageDesc,
) -> None:
    with patch("repod.models.package.PACKAGE_DESC_VERSIONS", {1: {"output_package_base_version": 9999}}):
        with raises(RuntimeError):
            packagedescv1.get_output_package_base(files=None)


@mark.parametrize(
    "output_package_base_type, expectation",
    [
        ("1", does_not_raise()),
        ("base", raises(RuntimeError)),
        ("9999", raises(RuntimeError)),
    ],
)
@mark.asyncio
async def test_output_package_base_v1_get_packages_as_models(
    packagedescv1: models.package.PackageDescV1,
    filesv1: models.package.FilesV1,
    outputpackagebasev1: models.OutputPackageBase,
    output_package_base_type: str,
    expectation: ContextManager[str],
) -> None:
    package_desc = packagedescv1
    files = filesv1
    output_package_base = outputpackagebasev1
    # remove all but the first package
    output_package_base.packages = output_package_base.packages[0:1]  # type: ignore[attr-defined]

    match output_package_base_type:
        case "base":
            output_package_base = models.OutputPackageBase()
        case "9999":
            output_package_base = OutputPackageBaseV9999()

    with expectation:
        assert [(package_desc, files)] == await output_package_base.get_packages_as_models()


@mark.parametrize(
    "name, expectation",
    [
        (".foo", raises(ValueError)),
        ("-foo", raises(ValueError)),
        ("foo'", raises(ValueError)),
        ("foo", does_not_raise()),
    ],
)
def test_name(name: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert name == common_models.Name(name=name).name


@mark.parametrize(
    "builddate, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_builddate(builddate: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert builddate == common_models.BuildDate(builddate=builddate).builddate


@mark.parametrize(
    "csize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_csize(csize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert csize == common_models.CSize(csize=csize).csize


@mark.parametrize(
    "isize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_isize(isize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isize == common_models.ISize(isize=isize).isize


def test_packager(default_packager: str, default_invalid_packager: str) -> None:
    with does_not_raise():
        common_models.Packager(packager=default_packager)
    with raises(ValidationError):
        common_models.Packager(packager=default_invalid_packager)


def test_get_desc_json_name() -> None:

    for identifier in DESC_JSON.keys():
        with does_not_raise():
            assert models.get_desc_json_name(key=identifier) == DESC_JSON[identifier][0]

    with raises(errors.RepoManagementFileError):
        models.get_desc_json_name(key="%FOO%")


def test_get_desc_json_field_type() -> None:

    for identifier in DESC_JSON.keys():
        with does_not_raise():
            assert models.get_desc_json_field_type(key=identifier) == DESC_JSON[identifier][1]

    with raises(errors.RepoManagementFileError):
        models.get_desc_json_field_type(key="%FOO%")


def test_get_files_json_name() -> None:

    for identifier in FILES_JSON.keys():
        with does_not_raise():
            assert models.get_files_json_name(key=identifier) == FILES_JSON[identifier][0]

    with raises(errors.RepoManagementFileError):
        models.get_files_json_name(key="%FOO%")


def test_get_files_json_field_type() -> None:

    for identifier in FILES_JSON.keys():
        with does_not_raise():
            assert models.get_files_json_field_type(key=identifier) == FILES_JSON[identifier][1]

    with raises(errors.RepoManagementFileError):
        models.get_files_json_field_type(key="%FOO%")


@mark.parametrize(
    "file_list, expectation",
    [
        (None, does_not_raise()),
        ([], does_not_raise()),
        (["foo"], does_not_raise()),
        (["home/foo"], raises(ValidationError)),
    ],
)
def test_file_list(file_list: Optional[List[str]], expectation: ContextManager[str]) -> None:
    with expectation:
        common_models.FileList(files=file_list)


def test_files_get_schema_version() -> None:
    model = models.Files()
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
            raises(errors.RepoManagementValidationError),
        ),
        (
            {"files": "foo"},
            raises(errors.RepoManagementValidationError),
        ),
        (
            {"foo": "bar"},
            raises(errors.RepoManagementValidationError),
        ),
    ],
)
def test_files_from_dict(data: Dict[str, Any], expectation: ContextManager[str]) -> None:
    with expectation:
        models.Files.from_dict(data=data)


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
            raises(errors.RepoManagementValidationError),
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
            with patch("repod.models.package.FILES_VERSIONS", files_versions):
                with patch("repod.models.package.DEFAULT_FILES_VERSION", default_files_version):
                    models.Files.from_dict(data=files_dict)
                    if emit_warning:
                        logging_warning_mock.assert_called_once()


def test_packagedesc_get_base() -> None:
    model = models.PackageDesc()
    with raises(RuntimeError):
        model.get_base()


def test_packagedesc_get_name() -> None:
    model = models.PackageDesc()
    with raises(RuntimeError):
        model.get_name()


def test_packagedesc_get_schema_version() -> None:
    model = models.PackageDesc()
    with raises(RuntimeError):
        model.get_schema_version()


def test_packagedesc_get_output_package() -> None:
    files = models.package.FilesV1(files=["foo", "bar", "baz"])
    model = models.PackageDesc()
    with raises(RuntimeError):
        model.get_output_package(files=files)


def test_packagedesc_get_output_package_base() -> None:
    files = models.package.FilesV1(files=["foo", "bar", "baz"])
    model = models.PackageDesc()
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
            raises(errors.RepoManagementValidationError),
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
            raises(errors.RepoManagementValidationError),
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
        models.PackageDesc.from_dict(data=data)


@mark.parametrize(
    "data, expectation",
    [
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": "someone",
                "packages": [],
                "version": create_default_full_version(),
            },
            raises(errors.RepoManagementValidationError),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": create_default_packager(),
                "packages": [],
                "schema_version": 1,
                "version": create_default_full_version(),
            },
            does_not_raise(),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": create_default_packager(),
                "packages": [],
                "schema_version": 0,
                "version": create_default_full_version(),
            },
            does_not_raise(),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": create_default_packager(),
                "packages": [],
                "schema_version": 9999,
                "version": create_default_full_version(),
            },
            raises(errors.RepoManagementValidationError),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": create_default_packager(),
                "packages": [
                    {
                        "arch": "any",
                        "backup": ["foo"],
                        "builddate": 1,
                        "checkdepends": [],
                        "conflicts": [],
                        "csize": 1,
                        "depends": ["bar"],
                        "desc": "something",
                        "filename": create_default_filename(),
                        "files": {"files": ["foo", "bar"]},
                        "groups": [],
                        "isize": 1,
                        "license": ["GPL"],
                        "md5sum": create_md5sum(),
                        "name": "foo",
                        "optdepends": [],
                        "pgpsig": create_base64_pgpsig(),
                        "provides": [],
                        "replaces": [],
                        "schema_version": 1,
                        "sha256sum": create_sha256sum(),
                        "url": create_url(),
                    },
                ],
                "schema_version": 1,
                "version": create_default_full_version(),
            },
            does_not_raise(),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": create_default_packager(),
                "packages": "foo",
                "schema_version": 1,
                "version": create_default_full_version(),
            },
            raises(errors.RepoManagementValidationError),
        ),
    ],
    ids=[
        "no schema version",
        "schema version 1, no packages",
        "schema version 0, no packages",
        "schema version 9999, no packages",
        "schema version 1, 1 package",
        "schema version 1, package is string",
    ],
)
def test_outputpackagebase_from_dict(data: Dict[str, Union[Any, List[Any]]], expectation: ContextManager[str]) -> None:
    with expectation:
        assert isinstance(models.OutputPackageBase.from_dict(data=data), models.OutputPackageBase)


@mark.parametrize(
    "output_package_base_type, expectation",
    [
        ("1", does_not_raise()),
        ("base", raises(RuntimeError)),
    ],
)
def test_outputpackagebase_add_packages(
    outputpackagebasev1: models.package.OutputPackageBaseV1,
    outputpackagev1: models.package.OutputPackageV1,
    output_package_base_type: str,
    expectation: ContextManager[str],
) -> None:
    match output_package_base_type:
        case "base":
            model = models.OutputPackageBase()
            input_ = models.package.OutputPackage()
        case "1":
            model = outputpackagebasev1
            input_ = outputpackagev1

    with expectation:
        model.add_packages(packages=[input_])


def test_outputpackagebase_get_version() -> None:
    model = models.OutputPackageBase()
    with raises(RuntimeError):
        model.get_version()


def test_export_schemas(tmp_path: Path) -> None:
    models.package.export_schemas(output=str(tmp_path))
    models.package.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        models.package.export_schemas(output="/foobar")

    with raises(RuntimeError):
        models.package.export_schemas(output=Path("/foobar"))
