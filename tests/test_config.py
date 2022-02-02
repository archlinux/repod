import shutil
import tempfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Any, ContextManager, Dict, Iterator, Tuple
from unittest.mock import Mock, call, patch

from pytest import fixture, raises

from repo_management import config, models


@fixture(scope="function")
def empty_dir() -> Iterator[Path]:
    directory = tempfile.mkdtemp()
    yield Path(directory)
    shutil.rmtree(directory)


@fixture(scope="function")
def empty_toml_files_in_dir(empty_dir: Path) -> Iterator[Path]:
    for i in range(5):
        tempfile.NamedTemporaryFile(suffix=".toml", dir=empty_dir, delete=False)
    yield empty_dir


@fixture(scope="function")
def empty_toml_file() -> Iterator[Path]:
    _, toml_file = tempfile.mkstemp(suffix=".toml")
    yield Path(toml_file)


@patch("tomli.load", return_value={})
def test_read_toml_configuration_settings(
    toml_load_mock: Mock,
    empty_toml_file: Path,
    empty_toml_files_in_dir: Path,
) -> None:
    with patch("repo_management.defaults.SETTINGS_LOCATION", empty_toml_file):
        config.read_toml_configuration_settings(Mock())
        with patch("repo_management.defaults.SETTINGS_OVERRIDE_LOCATION", empty_toml_files_in_dir):
            config.read_toml_configuration_settings(Mock())
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
            (Path("parent_repo_management"), "https://parent.foo.bar"),
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
            (True, Path("parent_repo_management/package_repo_base")),
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
            "management_repo": models.ManagementRepo(
                directory=empty_dir / request.param[1][0],
                url=request.param[1][1],
            )
            if request.param[1]
            else None,
            "repositories": [
                models.PackageRepo(
                    architecture=repo_settings[0] if repo_settings[0] else None,
                    name=repo_settings[1],
                    package_pool=(empty_dir / repo_settings[2]) if repo_settings[2] else None,
                    source_pool=(empty_dir / repo_settings[3]) if repo_settings[3] else None,
                    staging=repo_settings[4],
                    testing=repo_settings[5],
                    management_repo=models.ManagementRepo(
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
        settings = config.Settings(**settings_params[0])
        assert isinstance(settings, config.Settings)
        assert len(settings.repositories) > 0
