from contextlib import nullcontext as does_not_raise
from logging import DEBUG
from pathlib import Path
from typing import ContextManager, Tuple

from pytest import LogCaptureFixture, mark, raises

from repod.common.enums import RepoFileEnum
from repod.errors import RepoManagementFileError
from repod.repo.package import repofile


@mark.parametrize(
    "path_a, path_b, return_value, expectation",
    [
        (Path("/foo/bar/baz"), Path("/foo/bar/beh"), Path("/foo/bar"), does_not_raise()),
        (Path("/foo/bar/baz"), Path("/foo/bar/baz"), Path("/foo/bar/baz"), does_not_raise()),
        (Path("/foo/bar/baz/buh/bah"), Path("/foo/bar/beh"), Path("/foo/bar"), does_not_raise()),
        (Path("/foo/bar/baz"), Path("/foo/bar/beh/buh/bah"), Path("/foo/bar"), does_not_raise()),
        (Path("/baz"), Path("/beh"), Path("/"), does_not_raise()),
        (Path("/foo/bar/baz"), Path("beh"), None, raises(ValueError)),
        (Path("/foo/bar/baz"), Path(), None, raises(ValueError)),
        (Path("baz"), Path("/foo/bar/beh"), None, raises(ValueError)),
        (Path(), Path("/foo/bar/beh"), None, raises(ValueError)),
    ],
)
def test_shared_base_path(
    path_a: Path, path_b: Path, return_value: Path, expectation: ContextManager[str], caplog: LogCaptureFixture
) -> None:
    caplog.set_level(DEBUG)
    with expectation:
        assert repofile.shared_base_path(path_a=path_a, path_b=path_b) == return_value


@mark.parametrize(
    "path_a, path_b, return_value, expectation",
    [
        (Path("/foo/bar/baz/file"), Path("/foo/bar/beh/file"), Path("../baz/file"), does_not_raise()),
        (Path("/foo/bar/baz/file_a"), Path("/foo/bar/baz/file_b"), Path("file_a"), does_not_raise()),
        (Path("/foo/bar/baz/file_a"), Path("/foo/bar/baz/beh/file_b"), Path("../file_a"), does_not_raise()),
        (Path("/foo/bar/baz/file"), Path("file"), None, raises(ValueError)),
    ],
)
def test_relative_to_shared_base(
    path_a: Path, path_b: Path, return_value: Path, expectation: ContextManager[str], caplog: LogCaptureFixture
) -> None:
    caplog.set_level(DEBUG)
    with expectation:
        assert repofile.relative_to_shared_base(path_a=path_a, path_b=path_b) == return_value


@mark.parametrize(
    "file_symlink_equal, wrong_file_type, expectation",
    [
        (False, False, does_not_raise()),
        (True, False, raises(ValueError)),
        (False, True, raises(ValueError)),
    ],
)
def test_repofile(
    file_symlink_equal: bool,
    wrong_file_type: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    for file in default_package_file:
        if wrong_file_type:
            file_type = RepoFileEnum.PACKAGE if file.name.endswith(".sig") else RepoFileEnum.PACKAGE_SIGNATURE
        else:
            file_type = RepoFileEnum.PACKAGE if not file.name.endswith(".sig") else RepoFileEnum.PACKAGE_SIGNATURE

        file_path = file
        symlink_path = empty_dir / file.name

        if file_symlink_equal:
            symlink_path = file_path

        with expectation:
            assert repofile.RepoFile(file_type=file_type, file_path=file_path, symlink_path=symlink_path)


def test_repofile_get_file_type_regex_raises_on_invalid() -> None:
    with raises(RuntimeError):
        repofile.RepoFile.get_file_type_regex(file_type=None)


@mark.parametrize(
    "file_exists, exists, expectation",
    [
        (True, True, does_not_raise()),
        (False, True, raises(RepoManagementFileError)),
        (False, False, does_not_raise()),
        (True, False, raises(RepoManagementFileError)),
    ],
)
def test_repofile_check_file_path_exists(
    file_exists: bool,
    exists: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    if file_exists:
        file_path = default_package_file[0]
    else:
        file_path = empty_dir / default_package_file[0].name
    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=file_path,
        symlink_path=empty_dir / "foo" / default_package_file[0].name,
    )
    with expectation:
        file.check_file_path_exists(exists=exists)


@mark.parametrize(
    "symlink_exists, exists, expectation",
    [
        (True, True, does_not_raise()),
        (False, True, raises(RepoManagementFileError)),
        (False, False, does_not_raise()),
        (True, False, raises(RepoManagementFileError)),
    ],
)
def test_repofile_check_symlink_path_exists(
    symlink_exists: bool,
    exists: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    symlink_path = empty_dir / default_package_file[0].name
    if symlink_exists:
        symlink_path.touch()

    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=default_package_file[0],
        symlink_path=symlink_path,
    )
    with expectation:
        file.check_symlink_path_exists(exists=exists)


@mark.parametrize("source_exists, expectation", [(True, does_not_raise()), (False, raises(RepoManagementFileError))])
def test_repofile_copy_from(
    source_exists: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    source_path = default_package_file[0]
    destination_path = empty_dir / default_package_file[0].name
    if not source_exists:
        source_path = empty_dir / "bar" / default_package_file[0].name

    assert not destination_path.exists()

    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=destination_path,
        symlink_path=empty_dir / "foo" / default_package_file[0].name,
    )

    with expectation:
        file.copy_from(path=source_path)
        assert source_path.exists()
        assert destination_path.exists()


@mark.parametrize("source_exists, expectation", [(True, does_not_raise()), (False, raises(RepoManagementFileError))])
def test_repofile_move_from(
    source_exists: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    source_path = default_package_file[0]
    destination_path = empty_dir / default_package_file[0].name
    if not source_exists:
        source_path = empty_dir / "bar" / default_package_file[0].name

    assert not destination_path.exists()

    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=destination_path,
        symlink_path=empty_dir / "foo" / default_package_file[0].name,
    )

    with expectation:
        file.move_from(path=source_path)
        assert not source_path.exists()
        assert destination_path.exists()


@mark.parametrize(
    "link_exists, check, expectation",
    [
        (True, True, raises(RepoManagementFileError)),
        (True, False, raises(RepoManagementFileError)),
        (False, True, does_not_raise()),
        (False, False, does_not_raise()),
    ],
)
def test_repofile_link(
    link_exists: bool,
    check: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    symlink_path = empty_dir / default_package_file[0].name
    if link_exists:
        symlink_path.touch()
    else:
        assert not symlink_path.exists()

    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=default_package_file[0],
        symlink_path=symlink_path,
    )

    with expectation:
        file.link(check=check)
        assert symlink_path.exists()


@mark.parametrize(
    "link_exists, check, expectation",
    [
        (False, True, raises(RepoManagementFileError)),
        (False, False, does_not_raise()),
        (True, True, does_not_raise()),
        (True, False, does_not_raise()),
    ],
)
def test_repofile_unlink(
    link_exists: bool,
    check: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    symlink_path = empty_dir / default_package_file[0].name
    if link_exists:
        symlink_path.touch()
    else:
        assert not symlink_path.exists()

    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=default_package_file[0],
        symlink_path=symlink_path,
    )

    with expectation:
        file.unlink(check=check)
        assert not symlink_path.exists()


@mark.parametrize(
    "file_exists, symlink_exists, force, unlink, expectation",
    [
        (True, True, True, True, does_not_raise()),
        (True, True, False, True, does_not_raise()),
        (True, False, True, True, does_not_raise()),
        (False, False, True, True, does_not_raise()),
        (False, False, True, False, does_not_raise()),
        (False, False, False, False, raises(RepoManagementFileError)),
        (False, False, False, True, raises(RepoManagementFileError)),
    ],
)
def test_repofile_remove(
    file_exists: bool,
    symlink_exists: bool,
    force: bool,
    unlink: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    empty_dir: Path,
) -> None:
    caplog.set_level(DEBUG)

    file_path = default_package_file[0]
    symlink_path = empty_dir / default_package_file[0].name

    if not file_exists:
        file_path.unlink()

    if symlink_exists:
        symlink_path.touch()

    file = repofile.RepoFile(
        file_type=RepoFileEnum.PACKAGE,
        file_path=file_path,
        symlink_path=symlink_path,
    )

    with expectation:
        file.remove(force=force, unlink=unlink)
        assert not file_path.exists()

        if (unlink and symlink_exists) or not symlink_exists:
            assert not symlink_path.exists()
