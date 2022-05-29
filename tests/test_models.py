import shutil
import tempfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import (
    Any,
    ContextManager,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)
from unittest.mock import Mock, patch

from pydantic import ValidationError
from pytest import fixture, mark, raises

from repod import defaults, errors, models
from repod.common import models as common_models
from repod.models.repo import DESC_JSON, FILES_JSON
from tests.conftest import OutputPackageBaseV9999, PackageDescV9999


@fixture(scope="function")
def empty_dir() -> Iterator[Path]:
    directory = tempfile.mkdtemp()
    yield Path(directory)
    shutil.rmtree(directory)


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
                "arch": "foo",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": "foo",
                "isize": 1,
                "license": ["foo"],
                "md5sum": "foo",
                "name": "foo",
                "packager": "someone",
                "pgpsig": "signature",
                "sha256sum": "foo",
                "url": "url",
                "version": "1.0.0",
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
    "output_package, package_desc, files, expectation",
    [
        (
            models.package.OutputPackageV1(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                files=models.package.FilesV1(files=["foo", "bar"]),
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
            models.package.PackageDescV1(
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
            models.package.FilesV1(files=["foo", "bar"]),
            does_not_raise(),
        ),
        (
            models.package.OutputPackageV1(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                files=None,
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
            models.package.PackageDescV1(
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
            does_not_raise(),
        ),
        (
            models.package.OutputPackageV1(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                files=None,
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
            PackageDescV9999(),
            None,
            raises(errors.RepoManagementValidationError),
        ),
        (
            models.package.OutputPackageV1(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                files=None,
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
            PackageDescV9999(),
            None,
            raises(errors.RepoManagementValidationError),
        ),
    ],
)
def test_package_desc_get_output_package(
    output_package: models.package.OutputPackageV1,
    package_desc: models.package.PackageDescV1,
    files: Optional[models.Files],
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert output_package == package_desc.get_output_package(files)


def test_package_desc_get_output_package_inconsistent_schema_config() -> None:
    with patch("repod.models.package.PACKAGE_DESC_VERSIONS", {1: {"output_package_version": 9999}}):
        with raises(RuntimeError):
            models.package.PackageDescV1(
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
            ).get_output_package(files=None)


@mark.parametrize(
    "output_package_base, package_desc, files, expectation",
    [
        (
            models.package.OutputPackageBaseV1(
                base="foo",
                makedepends=["bar"],
                packager="someone",
                packages=[
                    models.package.OutputPackageV1(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=models.package.FilesV1(files=["foo", "bar"]),
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
                version="1.0.0",
            ),
            models.package.PackageDescV1(
                arch="foo",
                base="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                isize=1,
                license=["foo"],
                makedepends=["bar"],
                md5sum="foo",
                name="foo",
                packager="someone",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
                version="1.0.0",
            ),
            models.package.FilesV1(files=["foo", "bar"]),
            does_not_raise(),
        ),
        (
            models.package.OutputPackageBaseV1(
                base="foo",
                packager="someone",
                packages=[
                    models.package.OutputPackageV1(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=models.package.FilesV1(files=["foo", "bar"]),
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
                version="1.0.0",
            ),
            models.package.PackageDescV1(
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
                packager="someone",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
                version="1.0.0",
            ),
            models.package.FilesV1(files=["foo", "bar"]),
            does_not_raise(),
        ),
        (
            models.package.OutputPackageBaseV1(
                base="foo",
                packager="someone",
                packages=[
                    models.package.OutputPackageV1(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
                version="1.0.0",
            ),
            models.package.PackageDescV1(
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
                packager="someone",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
                version="1.0.0",
            ),
            None,
            does_not_raise(),
        ),
        (
            models.package.OutputPackageBaseV1(
                base="foo",
                packager="someone",
                packages=[
                    models.package.OutputPackageV1(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
                version="1.0.0",
            ),
            PackageDescV9999(),
            None,
            raises(errors.RepoManagementValidationError),
        ),
    ],
)
def test_package_desc_v1_get_output_package_base(
    output_package_base: models.package.OutputPackageBaseV1,
    package_desc: models.package.PackageDescV1,
    files: Optional[models.Files],
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert output_package_base == package_desc.get_output_package_base(files)


def test_package_desc_get_output_package_base_inconsistent_schema_config() -> None:
    with patch("repod.models.package.PACKAGE_DESC_VERSIONS", {1: {"output_package_base_version": 9999}}):
        with raises(RuntimeError):
            models.package.PackageDescV1(
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
            ).get_output_package_base(files=None)


@mark.parametrize(
    "models_list, output_package_base, expectation",
    [
        (
            [
                (
                    models.package.PackageDescV1(
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
                    models.package.FilesV1(files=["foo", "bar"]),
                ),
            ],
            models.package.OutputPackageBaseV1(
                base="foo",
                packager="foo",
                version="foo",
                packages=[
                    models.package.OutputPackageV1(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=models.package.FilesV1(files=["foo", "bar"]),
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
            ),
            does_not_raise(),
        ),
        (
            [],
            OutputPackageBaseV9999(),
            raises(RuntimeError),
        ),
        (
            [],
            models.OutputPackageBase(),
            raises(RuntimeError),
        ),
    ],
)
@mark.asyncio
async def test_output_package_base_get_packages_as_models(
    models_list: List[Tuple[models.package.PackageDesc, models.Files]],
    output_package_base: models.package.OutputPackageBase,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        assert models_list == await output_package_base.get_packages_as_models()


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


@mark.parametrize(
    "version, expectation",
    [
        ("1.2.3-0", raises(ValueError)),
        (".1.2.3-1", raises(ValueError)),
        ("-1.2.3-1", raises(ValueError)),
        (":1.2.3-1", raises(ValueError)),
        ("_1.2.3-1", raises(ValueError)),
        ("+1.2.3-1", raises(ValueError)),
        ("1.2.'3-1", raises(ValueError)),
        ("1.2.3-1", does_not_raise()),
        ("1:1.2.3-1", does_not_raise()),
        ("1:1.2.3r500.x.y.z.1-1", does_not_raise()),
    ],
)
def test_version_version_is_valid(version: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert version == common_models.Version(version=version).version


@mark.parametrize(
    "version, other_version, expectation",
    [
        ("1.2.3-1", "1.2.3-2", True),
        ("1.2.3-2", "1.2.3-1", False),
    ],
)
def test_version_is_older_than(version: str, other_version: str, expectation: bool) -> None:
    model = common_models.Version(version=version)
    assert model.is_older_than(other_version) is expectation


@mark.parametrize(
    "version, other_version, expectation",
    [
        ("1.2.3-1", "1.2.3-2", False),
        ("1.2.3-2", "1.2.3-1", True),
    ],
)
def test_version_is_newer_than(version: str, other_version: str, expectation: bool) -> None:
    model = common_models.Version(version=version)
    assert model.is_newer_than(other_version) is expectation


def test_architecture_validate_architecture() -> None:
    for arch in [None] + defaults.ARCHITECTURES:  # type:ignore
        assert models.Architecture(architecture=arch)

    with raises(ValueError):
        models.Architecture(architecture="foo")


@mark.parametrize(
    "url, expectation",
    [
        ("https://foo.bar", does_not_raise()),
        ("ssh://git@foo.bar", does_not_raise()),
        ("ssh://foo.bar", raises(ValueError)),
        ("http://foo.bar", raises(ValueError)),
    ],
)
def test_mangement_repo(
    url: str,
    expectation: ContextManager[str],
    empty_dir: Path,
) -> None:
    with expectation:
        assert models.ManagementRepo(
            directory=empty_dir,
            url=url,
        )


@patch(
    "os.access",
    Mock(side_effect=[False, False, True, True]),
)
@patch("repod.models.config.Path.exists", Mock(side_effect=[True, True, False, False, False, True, False]))
@patch("repod.models.config.Path.is_dir", Mock(side_effect=[False, True, True]))
@patch("repod.models.config.Path.parent", return_value=Mock())
def test_directory_validate_directory(parent_mock: Mock) -> None:
    parent_mock.exists.side_effect = [False, True, True, True]
    parent_mock.is_dir.side_effect = [False, True, True]
    with raises(ValueError):
        models.Directory(directory="foo")
    for _ in range(5):
        with raises(ValueError):
            models.Directory(directory="/foo")
    assert models.Directory(directory="/foo")
    assert models.Directory(directory="/foo")


@mark.parametrize(
    "name, staging, testing, package_pool, source_pool, management_repo, url, expectation",
    [
        (Path("foo"), None, None, False, False, False, None, does_not_raise()),
        (Path("foo"), Path("bar"), None, False, False, False, None, does_not_raise()),
        (Path("foo"), Path("bar"), Path("baz"), False, False, False, None, does_not_raise()),
        ("foo", None, None, False, False, False, None, does_not_raise()),
        ("foo", "bar", None, False, False, False, None, does_not_raise()),
        ("foo", "bar", "baz", False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), None, None, False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), Path("bar"), None, False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), Path("bar"), Path("baz"), False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), None, None, False, False, True, "https://foo.bar", does_not_raise()),
        (Path("foo-bar123"), Path("bar"), None, False, False, True, "https://foo.bar", does_not_raise()),
        (Path("foo-bar123"), Path("bar"), Path("baz"), False, False, True, "https://foo.bar", does_not_raise()),
        (Path("foo-bar123"), Path("bar"), Path("baz"), True, False, True, "https://foo.bar", raises(ValueError)),
        (Path("foo-bar123"), Path("bar"), Path("baz"), False, True, True, "https://foo.bar", raises(ValueError)),
        (Path(" foo"), None, None, False, False, False, None, raises(ValueError)),
        (Path("foo"), Path(" bar"), None, False, False, False, None, raises(ValueError)),
        (Path("foo"), Path("bar "), Path(" baz"), False, False, False, None, raises(ValueError)),
        (Path("foo"), Path("foo"), None, False, False, False, None, raises(ValueError)),
        (Path("foo"), None, Path("foo"), False, False, False, None, raises(ValueError)),
        (Path("foo"), None, None, True, True, False, None, raises(ValueError)),
        (Path("foo"), Path("bar"), None, True, True, False, None, raises(ValueError)),
        (Path("foo"), Path("bar"), Path("baz"), True, True, False, None, raises(ValueError)),
        (Path("foo"), Path("bar"), Path("bar"), False, False, False, None, raises(ValueError)),
        (Path("FOO"), None, None, False, False, False, None, raises(ValueError)),
        (Path("FOO"), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path("FOO"), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
        (Path("foo_BAR123"), None, None, False, False, False, None, raises(ValueError)),
        (Path("foo_BAR123"), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path("foo_BAR123"), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
        (Path("/foo"), None, None, False, False, False, None, raises(ValueError)),
        (Path("/foo"), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path("/foo"), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
        (Path(".foo"), None, None, False, False, False, None, raises(ValueError)),
        (Path(".foo"), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path(".foo"), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
        (Path("-foo"), None, None, False, False, False, None, raises(ValueError)),
        (Path("-foo"), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path("-foo"), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
        (Path("foo/bar"), None, None, False, False, False, None, raises(ValueError)),
        (Path("foo/bar"), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path("foo/bar"), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
        (Path("."), None, None, False, False, False, None, raises(ValueError)),
        (Path("."), Path("bar"), None, False, False, False, None, raises(ValueError)),
        (Path("."), Path("bar"), Path("baz"), False, False, False, None, raises(ValueError)),
    ],
)
def test_package_repo(
    name: Path,
    staging: Optional[Path],
    testing: Optional[Path],
    package_pool: bool,
    source_pool: bool,
    management_repo: bool,
    url: Optional[str],
    expectation: ContextManager[str],
    empty_dir: Path,
) -> None:
    with expectation:
        assert models.PackageRepo(
            name=name,
            testing=testing,
            staging=staging,
            package_pool=empty_dir if package_pool else None,
            source_pool=empty_dir if source_pool else None,
            management_repo=models.ManagementRepo(
                directory=empty_dir,
                url=url,
            )
            if management_repo
            else None,
        )


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
                "arch": "foo",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": "foo",
                "isize": 1,
                "license": ["foo"],
                "md5sum": "foo",
                "name": "foo",
                "packager": "foo",
                "pgpsig": "foo",
                "sha256sum": "foo",
                "url": "foo",
                "version": "foo",
            },
            does_not_raise(),
        ),
        (
            {
                "arch": "foo",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": "foo",
                "isize": 1,
                "license": ["foo"],
                "md5sum": "foo",
                "name": "foo",
                "packager": "foo",
                "pgpsig": "foo",
                "sha256sum": "foo",
                "url": "foo",
            },
            raises(errors.RepoManagementValidationError),
        ),
        (
            {
                "arch": "foo",
                "base": "foo",
                "builddate": 1,
                "csize": 1,
                "desc": "foo",
                "filename": "foo",
                "isize": 1,
                "license": ["foo"],
                "md5sum": "foo",
                "name": "foo",
                "packager": "foo",
                "pgpsig": "foo",
                "sha256sum": "foo",
                "url": "foo",
                "version": "foo",
                "foo": "bar",
            },
            raises(errors.RepoManagementValidationError),
        ),
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
                "version": "1.0.0",
            },
            raises(errors.RepoManagementValidationError),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": "someone",
                "packages": [],
                "schema_version": 1,
                "version": "1.0.0",
            },
            does_not_raise(),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": "someone",
                "packages": [],
                "schema_version": 0,
                "version": "1.0.0",
            },
            does_not_raise(),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": "someone",
                "packages": [],
                "schema_version": 9999,
                "version": "1.0.0",
            },
            raises(errors.RepoManagementValidationError),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": "someone",
                "packages": [
                    {
                        "arch": "foo",
                        "backup": ["foo"],
                        "builddate": 1,
                        "checkdepends": [],
                        "conflicts": [],
                        "csize": 1,
                        "depends": ["bar"],
                        "desc": "something",
                        "filename": "foo-1.0.0.pkg.tar.zst",
                        "files": {"files": ["foo", "bar"]},
                        "groups": [],
                        "isize": 1,
                        "license": ["GPL"],
                        "md5sum": "foo",
                        "name": "foo",
                        "optdepends": [],
                        "pgpsig": "signature",
                        "provides": [],
                        "replaces": [],
                        "schema_version": 1,
                        "sha256sum": "sha256sum",
                        "url": "https://archlinux.org",
                    },
                ],
                "schema_version": 1,
                "version": "1.0.0",
            },
            does_not_raise(),
        ),
        (
            {
                "base": "foo",
                "makedepends": ["bar"],
                "packager": "someone",
                "packages": "foo",
                "schema_version": 1,
                "version": "1.0.0",
            },
            raises(errors.RepoManagementValidationError),
        ),
    ],
)
def test_outputpackagebase_from_dict(data: Dict[str, Union[Any, List[Any]]], expectation: ContextManager[str]) -> None:
    with expectation:
        assert isinstance(models.OutputPackageBase.from_dict(data=data), models.OutputPackageBase)


def test_outputpackagebase_add_packages() -> None:
    model = models.OutputPackageBase()
    with raises(RuntimeError):
        model.add_packages(packages=[models.package.OutputPackage()])


def test_outputpackagebase_get_version() -> None:
    model = models.OutputPackageBase()
    with raises(RuntimeError):
        model.get_version()


def test_export_schemas() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        models.package.export_schemas(output=str(tmp))
        models.package.export_schemas(output=tmp)

    with raises(RuntimeError):
        models.package.export_schemas(output="/foobar")

    with raises(RuntimeError):
        models.package.export_schemas(output=Path("/foobar"))
