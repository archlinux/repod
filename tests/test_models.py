import shutil
import tempfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import ContextManager, Iterator, List, Optional, Tuple
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

from repo_management import defaults, models


@fixture(scope="function")
def empty_dir() -> Iterator[Path]:
    directory = tempfile.mkdtemp()
    yield Path(directory)
    shutil.rmtree(directory)


@mark.parametrize(
    "output_package, package_desc, files",
    [
        (
            models.OutputPackage(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                files=["foo", "bar"],
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
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
            models.OutputPackage(
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
def test_package_desc_get_output_package(
    output_package: models.OutputPackage,
    package_desc: models.PackageDesc,
    files: Optional[models.Files],
) -> None:
    assert output_package == package_desc.get_output_package(files)


@mark.parametrize(
    "models_list, output_package_base",
    [
        (
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
            ],
            models.OutputPackageBase(
                base="foo",
                packager="foo",
                version="foo",
                packages=[
                    models.OutputPackage(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=["foo", "bar"],
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
        ),
    ],
)
@mark.asyncio
async def test_output_package_base_get_packages_as_models(
    models_list: List[Tuple[models.PackageDesc, models.Files]],
    output_package_base: models.OutputPackageBase,
) -> None:
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
        assert name == models.Name(name=name).name


@mark.parametrize(
    "builddate, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_builddate(builddate: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert builddate == models.BuildDate(builddate=builddate).builddate


@mark.parametrize(
    "csize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_csize(csize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert csize == models.CSize(csize=csize).csize


@mark.parametrize(
    "isize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_isize(isize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isize == models.ISize(isize=isize).isize


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
        assert version == models.Version(version=version).version


@mark.parametrize(
    "version, other_version, expectation",
    [
        ("1.2.3-1", "1.2.3-2", True),
        ("1.2.3-2", "1.2.3-1", False),
    ],
)
def test_version_is_older_than(version: str, other_version: str, expectation: bool) -> None:
    model = models.Version(version=version)
    assert model.is_older_than(other_version) is expectation


@mark.parametrize(
    "version, other_version, expectation",
    [
        ("1.2.3-1", "1.2.3-2", False),
        ("1.2.3-2", "1.2.3-1", True),
    ],
)
def test_version_is_newer_than(version: str, other_version: str, expectation: bool) -> None:
    model = models.Version(version=version)
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
@patch("repo_management.models.Path.exists", Mock(side_effect=[True, True, False, False, False, True, False]))
@patch("repo_management.models.Path.is_dir", Mock(side_effect=[False, True, True]))
@patch("repo_management.models.Path.parent", return_value=Mock())
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
