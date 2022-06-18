from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, ContextManager, Dict, Iterator, Optional, Tuple
from unittest.mock import Mock, call, patch

from pytest import fixture, mark, raises

from repod.config import settings


def test_architecture_validate_architecture(default_arch: str) -> None:
    assert settings.Architecture(architecture=default_arch)

    with raises(ValueError):
        settings.Architecture(architecture="foo")


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
        assert settings.ManagementRepo(
            directory=empty_dir,
            url=url,
        )


@patch(
    "os.access",
    Mock(side_effect=[False, False, True, True]),
)
@patch("repod.config.settings.Path.exists", Mock(side_effect=[True, True, False, False, False, True, False]))
@patch("repod.config.settings.Path.is_dir", Mock(side_effect=[False, True, True]))
@patch("repod.config.settings.Path.parent", return_value=Mock())
def test_validate_directory(parent_mock: Mock) -> None:
    parent_mock.exists.side_effect = [False, True, True, True]
    parent_mock.is_dir.side_effect = [False, True, True]
    with raises(ValueError):
        settings.validate_directory(directory=Path("foo"))
    for _ in range(5):
        with raises(ValueError):
            settings.validate_directory(directory=Path("/foo"))
    assert settings.validate_directory(directory=Path("/foo"))
    assert settings.validate_directory(directory=Path("/foo"))


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
        assert settings.PackageRepo(
            name=name,
            testing=testing,
            staging=staging,
            package_pool=empty_dir if package_pool else None,
            source_pool=empty_dir if source_pool else None,
            management_repo=settings.ManagementRepo(
                directory=empty_dir,
                url=url,
            )
            if management_repo
            else None,
        )


@patch("tomli.load", return_value={})
def test_read_toml_configuration_settings(
    toml_load_mock: Mock,
    empty_toml_file: Path,
    empty_toml_files_in_dir: Path,
) -> None:
    with patch("repod.config.settings.SETTINGS_LOCATION", empty_toml_file):
        settings.read_toml_configuration_settings(Mock())
        with patch("repod.config.settings.SETTINGS_OVERRIDE_LOCATION", empty_toml_files_in_dir):
            settings.read_toml_configuration_settings(Mock())
            toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))


@fixture(
    scope="function",
    params=[
        # single_repo_with_overrides
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    "x86_64",
                    Path("foo"),
                    Path("child_package_pool"),
                    Path("child_source_pool"),
                    Path("staging"),
                    Path("testing"),
                    (Path("child_management_repo"), "https://child.foo.bar"),
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            does_not_raise(),
        ),
        # single_repo_with_no_overrides
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            does_not_raise(),
        ),
        # raise_on_no_repo
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_no_architecture
        (
            None,
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_repo_source_base
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("same")),
            (True, Path("same")),
            raises(ValueError),
        ),
        # raise_on_no_management_repo
        (
            "x86_64",
            None,
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_no_package_pool
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            None,
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_no_source_pool
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            None,
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_no_package_repo_base
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (False, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_no_source_repo_base
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (False, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_repo_name_staging_name
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    None,
                    Path("bar"),
                    None,
                    None,
                    Path("foo"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_repo_name_testing_name
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    None,
                    Path("bar"),
                    None,
                    None,
                    None,
                    Path("foo"),
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_repo_name_management_repo_dir
        (
            "x86_64",
            (Path("package_repo_base/foo/x86_64"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_repo_staging_management_repo_dir
        (
            "x86_64",
            (Path("package_repo_base/bar/x86_64"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_repo_testing_management_repo_dir
        (
            "x86_64",
            (Path("package_repo_base/bar/x86_64"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    Path("bar"),
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_repo_name_below_management_repo_dir
        (
            "x86_64",
            (Path("parent_repod"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("parent_repod/package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_staging_testing_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
                (
                    None,
                    Path("baz"),
                    None,
                    None,
                    None,
                    Path("bar"),
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_testing_staging_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    Path("testing"),
                    None,
                ),
                (
                    None,
                    Path("bar"),
                    None,
                    None,
                    Path("testing"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_management_repo_dir_below_package_repo_base_dir
        (
            "x86_64",
            (Path("package_repo_base/bar/x86_64"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_management_repo_dir_below_source_repo_base_dir
        (
            "x86_64",
            (Path("source_repo_base/bar/x86_64/parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_management_repo_dir_below_package_pool_dir
        (
            "x86_64",
            (Path("parent_package_pool/parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_management_repo_dir_below_source_pool_dir
        (
            "x86_64",
            (Path("parent_source_pool/parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_pool_dir_below_source_pool_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_source_pool/parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_pool_dir_below_management_repo_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_management_repo/parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_pool_dir_below_package_repo_base_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("package_repo_base/parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_pool_dir_below_source_repo_base_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("source_repo_base/parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_pool_dir_below_package_pool_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_package_pool/parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_pool_dir_below_management_repo_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_management_repo/parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_pool_dir_below_package_repo_base_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("package_repo_base/parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_pool_dir_below_source_repo_base_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    Path("bar"),
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("source_repo_base/parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_duplicate_repositories
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_conflicting_package_repo_base_source_repo_base
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("package_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_repo_base_below_source_repo_base_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("source_repo_base/package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_repo_base_below_management_repo_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("parent_management_repo/package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_repo_base_below_package_pool_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("parent_package_pool/package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_package_repo_base_below_source_pool_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("parent_source_pool/package_repo_base")),
            (True, Path("source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_repo_base_below_package_repo_base
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("package_repo_base/source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_repo_base_below_management_repo_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("parent_management_repo/source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_repo_base_below_package_pool_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("parent_package_pool/source_repo_base")),
            raises(ValueError),
        ),
        # raise_on_source_repo_base_below_source_pool_dir
        (
            "x86_64",
            (Path("parent_management_repo"), "https://parent.foo.bar"),
            [
                (
                    None,
                    Path("foo"),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
            Path("parent_package_pool"),
            Path("parent_source_pool"),
            (True, Path("package_repo_base")),
            (True, Path("parent_source_pool/source_repo_base")),
            raises(ValueError),
        ),
    ],
    ids=[
        "single_repo_with_overrides",
        "single_repo_with_no_overrides",
        "raise_on_no_repo",
        "raise_on_no_architecture",
        "raise_on_conflicting_repo_source_base",
        "raise_on_no_management_repo",
        "raise_on_no_package_pool",
        "raise_on_no_source_pool",
        "raise_on_no_package_repo_base",
        "raise_on_no_source_repo_base",
        "raise_on_conflicting_repo_name_staging_name",
        "raise_on_conflicting_repo_name_testing_name",
        "raise_on_conflicting_repo_name_management_repo_dir",
        "raise_on_conflicting_repo_staging_management_repo_dir",
        "raise_on_conflicting_repo_testing_management_repo_dir",
        "raise_on_repo_name_below_management_repo_dir",
        "raise_on_conflicting_staging_testing_dir",
        "raise_on_conflicting_testing_staging_dir",
        "raise_on_management_repo_dir_below_package_repo_base_dir",
        "raise_on_management_repo_dir_below_source_repo_base_dir",
        "raise_on_management_repo_dir_below_package_pool_dir",
        "raise_on_management_repo_dir_below_source_pool_dir",
        "raise_on_package_pool_dir_below_source_pool_dir",
        "raise_on_package_pool_dir_below_management_repo_dir",
        "raise_on_package_pool_dir_below_package_repo_base_dir",
        "raise_on_package_pool_dir_below_source_repo_base_dir",
        "raise_on_source_pool_dir_below_package_pool_dir",
        "raise_on_source_pool_dir_below_management_repo_dir",
        "raise_on_source_pool_dir_below_package_repo_base_dir",
        "raise_on_source_pool_dir_below_source_repo_base_dir",
        "raise_on_duplicate_repositories",
        "raise_on_conflicting_package_repo_base_source_repo_base",
        "raise_on_package_repo_base_below_source_repo_base_dir",
        "raise_on_package_repo_base_below_management_repo_dir",
        "raise_on_package_repo_base_below_package_pool_dir",
        "raise_on_package_repo_base_below_source_pool_dir",
        "raise_on_source_repo_base_below_package_repo_base",
        "raise_on_source_repo_base_below_management_repo_dir",
        "raise_on_source_repo_base_below_package_pool_dir",
        "raise_on_source_repo_base_below_source_pool_dir",
    ],
)
def settings_params(request: Any, empty_dir: Path) -> Iterator[Tuple[Dict[str, Any], ContextManager[str]]]:
    # create management repository directory
    if request.param[1]:
        Path(empty_dir / request.param[1][0]).mkdir(parents=True, exist_ok=True)
    # create management repository directories for each repository
    for repo in request.param[2]:
        if repo[6]:
            Path(empty_dir / repo[6][0]).mkdir(parents=True, exist_ok=True)
    # create package pool directory
    if request.param[3]:
        Path(empty_dir / request.param[3]).mkdir(parents=True, exist_ok=True)
    # create source pool directory
    if request.param[4]:
        Path(empty_dir / request.param[4]).mkdir(parents=True, exist_ok=True)
    # create package repository base directory
    if request.param[5][0]:
        Path(empty_dir / request.param[5][1]).mkdir(parents=True, exist_ok=True)
    # create source repository base directory
    if request.param[6][0]:
        Path(empty_dir / request.param[6][1]).mkdir(parents=True, exist_ok=True)

    yield (
        {
            "architecture": request.param[0] or None,
            "management_repo": settings.ManagementRepo(
                directory=empty_dir / request.param[1][0],
                url=request.param[1][1],
            )
            if request.param[1]
            else None,
            "repositories": [
                settings.PackageRepo(
                    architecture=repo_settings[0] if repo_settings[0] else None,
                    name=repo_settings[1],
                    package_pool=(empty_dir / repo_settings[2]) if repo_settings[2] else None,
                    source_pool=(empty_dir / repo_settings[3]) if repo_settings[3] else None,
                    staging=repo_settings[4],
                    testing=repo_settings[5],
                    management_repo=settings.ManagementRepo(
                        directory=empty_dir / repo_settings[6][0],
                        url=repo_settings[6][1],
                    )
                    if repo_settings[6]
                    else None,
                )
                for repo_settings in request.param[2]
            ],
            "package_pool": empty_dir / request.param[3] if request.param[3] else None,
            "source_pool": empty_dir / request.param[4] if request.param[4] else None,
            "package_repo_base": empty_dir / request.param[5][1] if request.param[5][0] else request.param[5][1],
            "source_repo_base": empty_dir / request.param[6][1] if request.param[6][0] else request.param[6][1],
        },
        request.param[7],
    )


def test_settings(
    settings_params: Tuple[Dict[str, Any], ContextManager[str]],
) -> None:
    with settings_params[1]:
        conf = settings.Settings(**settings_params[0])
        assert isinstance(conf, settings.Settings)
        assert len(conf.repositories) > 0
