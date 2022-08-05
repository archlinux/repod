from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from pathlib import Path
from typing import Any, ContextManager, Dict, List, Optional, Union

from pytest import mark, raises

from repod.common.enums import FilesVersionEnum, PackageDescVersionEnum
from repod.errors import RepoManagementFileError, RepoManagementValidationError
from repod.files.buildinfo import BuildInfo
from repod.files.package import Package
from repod.repo.management import outputpackage
from repod.repo.package import syncdb
from tests.conftest import (
    BuildInfoV9999,
    OutputPackageBaseV9999,
    create_base64_pgpsig,
    create_default_filename,
    create_default_full_version,
    create_default_packager,
    create_md5sum,
    create_sha256sum,
    create_url,
)


def test_outputpackage_from_packagev1(packagev1: Package) -> None:
    outputpackage.OutputPackage.from_package(package=packagev1)


def test_outputpackage_from_package() -> None:
    with raises(RuntimeError):
        outputpackage.OutputPackage.from_package(package=Package())


@mark.parametrize(
    "outputpackagebase_version, packagedesc_version, files_version, expectation",
    [
        (1, PackageDescVersionEnum.ONE, FilesVersionEnum.ONE, does_not_raise()),
        (1, PackageDescVersionEnum.TWO, FilesVersionEnum.ONE, does_not_raise()),
        (None, PackageDescVersionEnum.ONE, FilesVersionEnum.ONE, raises(RuntimeError)),
        (9999, PackageDescVersionEnum.ONE, FilesVersionEnum.ONE, raises(RuntimeError)),
    ],
)
@mark.asyncio
async def test_output_package_base_v1_get_packages_as_models(
    packagedescv1: outputpackage.PackageDescV1,
    packagedescv2: outputpackage.PackageDescV2,
    filesv1: syncdb.FilesV1,
    outputpackagebasev1: outputpackage.OutputPackageBase,
    outputpackagebase_version: Optional[int],
    packagedesc_version: PackageDescVersionEnum,
    files_version: FilesVersionEnum,
    expectation: ContextManager[str],
) -> None:
    packagedesc: syncdb.PackageDesc
    match packagedesc_version:
        case PackageDescVersionEnum.ONE:
            packagedesc = packagedescv1
        case PackageDescVersionEnum.TWO:
            packagedesc = packagedescv2

    files: syncdb.Files
    match files_version:
        case FilesVersionEnum.ONE:
            files = filesv1

    outputpackagebase: outputpackage.OutputPackageBase
    match outputpackagebase_version:
        case None:
            output_package_base = outputpackage.OutputPackageBase()
        case 1:
            output_package_base = outputpackagebasev1
            # remove all but the first package
            output_package_base.packages = output_package_base.packages[0:1]  # type: ignore[attr-defined]
        case 9999:
            output_package_base = OutputPackageBaseV9999()

    with expectation:
        assert [(packagedesc, files)] == await output_package_base.get_packages_as_models(
            packagedesc_version=packagedesc_version,
            files_version=files_version,
        )


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
            raises(RepoManagementValidationError),
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
            raises(RepoManagementValidationError),
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
            raises(RepoManagementValidationError),
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
        assert isinstance(outputpackage.OutputPackageBase.from_dict(data=data), outputpackage.OutputPackageBase)


@mark.asyncio
async def test_outputpackagebase_from_file(broken_json_file: Path, invalid_json_file: Path) -> None:
    with raises(RepoManagementFileError):
        await outputpackage.OutputPackageBase.from_file(path=broken_json_file)
    with raises(RepoManagementValidationError):
        await outputpackage.OutputPackageBase.from_file(path=invalid_json_file)


def test_outputpackagebase_from_package() -> None:
    with raises(RuntimeError):
        outputpackage.OutputPackageBase.from_package(packages=[Package()])


def test_outputpackagebase_from_packagev1(packagev1: Package) -> None:
    assert outputpackage.OutputPackageBase.from_package(packages=[packagev1])


def test_outputpackagebase_from_package_raise_on_no_package() -> None:
    with raises(ValueError):
        assert outputpackage.OutputPackageBase.from_package(packages=[])


def test_outputpackagebase_from_packagev1_raise_on_multiple_pkgbases(packagev1: Package) -> None:
    package_b = deepcopy(packagev1)
    package_b.buildinfo.pkgbase = "wrong"  # type: ignore[attr-defined]
    with raises(ValueError):
        outputpackage.OutputPackageBase.from_package(packages=[packagev1, package_b])


def test_outputpackagebase_from_packagev1_raise_on_duplicate_names(packagev1: Package) -> None:
    package_b = deepcopy(packagev1)
    with raises(ValueError):
        outputpackage.OutputPackageBase.from_package(packages=[packagev1, package_b])


def test_outputpackagebase_from_packagev1_raise_on_version_mismatch(packagev1: Package) -> None:
    package_b = deepcopy(packagev1)
    package_b.pkginfo.name = "different"  # type: ignore[attr-defined]
    package_b.pkginfo.version = "wrong"  # type: ignore[attr-defined]
    with raises(ValueError):
        outputpackage.OutputPackageBase.from_package(packages=[packagev1, package_b])


def test_outputpackagebase_from_packagev1_raise_on_pkgtype_mismatch(packagev1_pkginfov2: Package) -> None:
    package_b = deepcopy(packagev1_pkginfov2)
    package_b.pkginfo.name = "different"  # type: ignore[attr-defined]
    package_b.pkginfo.pkgtype = "debug"  # type: ignore[attr-defined]
    with raises(ValueError):
        outputpackage.OutputPackageBase.from_package(packages=[packagev1_pkginfov2, package_b])


@mark.parametrize(
    "output_package_base_type, expectation",
    [
        ("1", does_not_raise()),
        ("base", raises(RuntimeError)),
    ],
)
def test_outputpackagebase_add_packages(
    outputpackagebasev1: outputpackage.OutputPackageBaseV1,
    outputpackagev1: outputpackage.OutputPackageV1,
    output_package_base_type: str,
    expectation: ContextManager[str],
) -> None:
    match output_package_base_type:
        case "base":
            model = outputpackage.OutputPackageBase()
            input_ = outputpackage.OutputPackage()
        case "1":
            model = outputpackagebasev1
            input_ = outputpackagev1

    with expectation:
        model.add_packages(packages=[input_])


def test_outputpackagebase_get_version() -> None:
    model = outputpackage.OutputPackageBase()
    with raises(RuntimeError):
        model.get_version()


def test_export_schemas(tmp_path: Path) -> None:
    outputpackage.export_schemas(output=str(tmp_path))
    outputpackage.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        outputpackage.export_schemas(output="/foobar")

    with raises(RuntimeError):
        outputpackage.export_schemas(output=Path("/foobar"))


@mark.parametrize(
    "buildinfo_version, expectation",
    [
        (1, does_not_raise()),
        (2, does_not_raise()),
        (9999, raises(RuntimeError)),
    ],
)
def test_outputbuildinfo_from_buildinfo(
    buildinfo_version: int,
    expectation: ContextManager[str],
    valid_buildinfov1: BuildInfo,
    valid_buildinfov2: BuildInfo,
) -> None:
    match buildinfo_version:
        case 1:
            buildinfo = valid_buildinfov1
        case 2:
            buildinfo = valid_buildinfov2
        case 9999:
            buildinfo = BuildInfoV9999()

    with expectation:
        outputbuildinfo = outputpackage.OutputBuildInfo.from_buildinfo(buildinfo=buildinfo)

        match buildinfo_version:
            case 1:
                assert isinstance(outputbuildinfo, outputpackage.OutputBuildInfoV1)
            case 2:
                assert isinstance(outputbuildinfo, outputpackage.OutputBuildInfoV2)
