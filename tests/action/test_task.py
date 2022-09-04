from contextlib import nullcontext as does_not_raise
from logging import DEBUG
from pathlib import Path
from typing import ContextManager, List, Optional, Tuple
from unittest.mock import Mock, patch

from orjson import JSONEncodeError
from pydantic import ValidationError
from pytest import LogCaptureFixture, mark, raises

from repod.action import task
from repod.action.check import PacmanKeyPackagesSignatureVerificationCheck
from repod.common.enums import ActionStateEnum, PkgVerificationTypeEnum, RepoFileEnum
from repod.config import UserSettings
from repod.config.defaults import DEFAULT_ARCHITECTURE, DEFAULT_NAME
from repod.errors import RepoManagementFileError
from repod.repo.management import OutputPackageBase


@mark.parametrize(
    "path, expectation",
    [
        (Path("/foo.tmp"), does_not_raise()),
        (Path("/foo"), raises(ValidationError)),
        (Path("foo"), raises(ValidationError)),
    ],
)
def test_sourcedestination_validate_source(path: Path, expectation: ContextManager[str]) -> None:
    with expectation:
        task.SourceDestination(source=path, destination=Path("/foo"), destination_backup=Path("/foo.bkp"))


@mark.parametrize(
    "path, expectation",
    [
        (Path("/foo"), does_not_raise()),
        (Path("/foo.tmp"), raises(ValidationError)),
        (Path("/foo.bkp"), raises(ValidationError)),
        (Path("foo"), raises(ValidationError)),
    ],
)
def test_sourcedestination_validate_destination(path: Path, expectation: ContextManager[str]) -> None:
    with expectation:
        task.SourceDestination(source=Path("/foo.tmp"), destination=path, destination_backup=Path("/foo.bkp"))


@mark.parametrize(
    "path, expectation",
    [
        (Path("/foo.bkp"), does_not_raise()),
        (Path("/foo.tmp"), raises(ValidationError)),
        (Path("foo"), raises(ValidationError)),
    ],
)
def test_sourcedestination_validate_destination_backup(path: Path, expectation: ContextManager[str]) -> None:
    with expectation:
        task.SourceDestination(source=Path("/foo.tmp"), destination=Path("/foo"), destination_backup=path)


@mark.parametrize(
    "package_verification, with_signature, add_dependencies",
    [
        (None, True, False),
        (None, False, False),
        (None, True, True),
        (None, False, True),
        (PkgVerificationTypeEnum.PACMANKEY, False, False),
        (PkgVerificationTypeEnum.PACMANKEY, True, False),
        (PkgVerificationTypeEnum.PACMANKEY, False, True),
        (PkgVerificationTypeEnum.PACMANKEY, True, True),
    ],
)
def test_createoutputpackagebasestask(
    package_verification: Optional[PkgVerificationTypeEnum],
    with_signature: bool,
    add_dependencies: bool,
    default_package_file: Tuple[Path, ...],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [Mock()]

    task_ = task.CreateOutputPackageBasesTask(
        package_paths=[default_package_file[0]],
        with_signature=with_signature,
        package_verification=package_verification,
        debug_repo=False,
        dependencies=dependencies if add_dependencies else None,
    )

    if package_verification == PkgVerificationTypeEnum.PACMANKEY and with_signature:
        found_check = False
        for check in task_.pre_checks:
            if isinstance(check, PacmanKeyPackagesSignatureVerificationCheck):
                found_check = True

        assert found_check

    if add_dependencies:
        assert task_.dependencies == dependencies


@mark.parametrize(
    "with_signature, package_from_file_raises, outputpackagebase_from_package_raises, return_value",
    [
        (True, False, False, ActionStateEnum.SUCCESS_TASK),
        (True, True, False, ActionStateEnum.FAILED_TASK),
        (True, False, True, ActionStateEnum.FAILED_TASK),
        (False, False, False, ActionStateEnum.SUCCESS_TASK),
        (False, True, False, ActionStateEnum.FAILED_TASK),
        (False, False, True, ActionStateEnum.FAILED_TASK),
    ],
)
def test_createoutputpackagebasestask_do(
    with_signature: bool,
    package_from_file_raises: bool,
    outputpackagebase_from_package_raises: bool,
    return_value: ActionStateEnum,
    default_package_file: Tuple[Path, ...],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    task_ = task.CreateOutputPackageBasesTask(
        package_paths=[default_package_file[0]],
        with_signature=with_signature,
        debug_repo=False,
        package_verification=None,
    )

    if package_from_file_raises:
        with patch("repod.action.task.Package.from_file", side_effect=RepoManagementFileError):
            assert task_.do() == return_value
    elif outputpackagebase_from_package_raises:
        with patch("repod.action.task.OutputPackageBase.from_package", side_effect=ValueError):
            assert task_.do() == return_value
    else:
        assert task_.do() == return_value

    if return_value == ActionStateEnum.SUCCESS_TASK:
        assert isinstance(task_.pkgbases[0], OutputPackageBase)


def test_createoutputpackagebasestask_undo(
    default_package_file: Tuple[Path, ...],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    task_ = task.CreateOutputPackageBasesTask(
        package_paths=[default_package_file[0]],
        with_signature=True,
        debug_repo=False,
        package_verification=None,
    )

    task_.do()
    assert isinstance(task_.pkgbases[0], OutputPackageBase)

    assert task_.undo() == ActionStateEnum.NOT_STARTED
    assert task_.pkgbases == []


@mark.parametrize(
    "add_pkgbases, add_dependencies, expectation",
    [
        (True, False, does_not_raise()),
        (False, True, does_not_raise()),
        (False, False, raises(RuntimeError)),
    ],
)
def test_printoutputpackagebasestask(
    add_pkgbases: bool,
    add_dependencies: bool,
    expectation: ContextManager[str],
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [
        Mock(),
        Mock(spec=task.CreateOutputPackageBasesTask),
        Mock(),
    ]

    with expectation:
        task_ = task.PrintOutputPackageBasesTask(
            dumps_option=0,
            pkgbases=[outputpackagebasev1] if add_pkgbases else None,
            dependencies=dependencies if add_dependencies else None,
        )

    if expectation is does_not_raise():
        assert task_.dumps_option == 0

        if add_pkgbases and not add_dependencies:
            assert task_.pkgbases == [outputpackagebasev1]
            assert not task_.input_from_dependency
            assert not task_.dependencies

        if add_dependencies:
            assert task_.dependencies == dependencies
            assert task_.pkgbases == []
            assert task_.input_from_dependency


@mark.parametrize(
    "add_pkgbases, add_dependencies, dependency_state, dumps_raises, return_value",
    [
        (True, False, ActionStateEnum.SUCCESS, False, ActionStateEnum.SUCCESS_TASK),
        (False, True, ActionStateEnum.SUCCESS, False, ActionStateEnum.SUCCESS_TASK),
        (True, True, ActionStateEnum.SUCCESS, False, ActionStateEnum.SUCCESS_TASK),
        (True, False, ActionStateEnum.SUCCESS, True, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, ActionStateEnum.FAILED_TASK),
        (True, True, ActionStateEnum.SUCCESS, True, ActionStateEnum.FAILED_TASK),
        (True, True, ActionStateEnum.FAILED_TASK, False, ActionStateEnum.FAILED_DEPENDENCY),
    ],
)
def test_printoutputpackagebasestask_do(
    add_pkgbases: bool,
    add_dependencies: bool,
    dependency_state: ActionStateEnum,
    dumps_raises: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [
        Mock(),
        Mock(
            spec=task.CreateOutputPackageBasesTask,
            state=dependency_state,
            pkgbases=[outputpackagebasev1],
        ),
        Mock(),
    ]

    task_ = task.PrintOutputPackageBasesTask(
        dumps_option=0,
        pkgbases=[outputpackagebasev1] if add_pkgbases else None,
        dependencies=dependencies if add_dependencies else None,
    )
    if dumps_raises:
        with patch("repod.action.task.dumps", side_effect=JSONEncodeError):
            assert task_.do() == return_value
    else:
        assert task_.do() == return_value


@mark.parametrize(
    "add_pkgbases, add_dependencies, do",
    [
        (True, True, True),
        (True, False, True),
        (False, True, True),
        (True, True, False),
        (True, False, False),
        (False, True, False),
    ],
)
def test_printoutputpackagebasestask_undo(
    add_pkgbases: bool,
    add_dependencies: bool,
    do: bool,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [
        Mock(
            spec=task.CreateOutputPackageBasesTask,
            state=ActionStateEnum.SUCCESS,
            pkgbases=[outputpackagebasev1],
            undo=Mock(return_value=ActionStateEnum.NOT_STARTED),
        ),
    ]

    task_ = task.PrintOutputPackageBasesTask(
        dumps_option=0,
        pkgbases=[outputpackagebasev1] if add_pkgbases else None,
        dependencies=dependencies if add_dependencies else None,
    )

    if do:
        assert task_.do() == ActionStateEnum.SUCCESS_TASK

    assert task_.undo() == ActionStateEnum.NOT_STARTED

    if add_pkgbases and not add_dependencies:
        assert task_.pkgbases == [outputpackagebasev1]

    if add_dependencies:
        assert task_.pkgbases == []


@mark.parametrize(
    "add_pkgbases, add_dependencies, expectation",
    [
        (True, True, does_not_raise()),
        (True, False, does_not_raise()),
        (False, True, does_not_raise()),
        (False, False, raises(RuntimeError)),
    ],
)
def test_writeoutputpackagebasestotmpfileindirtask(
    add_pkgbases: bool,
    add_dependencies: bool,
    expectation: ContextManager[str],
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [
        Mock(),
        Mock(spec=task.CreateOutputPackageBasesTask, pkgbases=outputpackagebasev1, state=ActionStateEnum.SUCCESS),
        Mock(),
    ]

    with expectation:
        task_ = task.WriteOutputPackageBasesToTmpFileInDirTask(
            directory=tmp_path,
            pkgbases=[outputpackagebasev1] if add_pkgbases else None,
            dependencies=dependencies if add_dependencies else None,
        )
        assert task_.directory == tmp_path
        assert not task_.filenames

        if add_dependencies:
            assert task_.dependencies == dependencies
            assert task_.pkgbases == []
        else:
            assert task_.pkgbases == [outputpackagebasev1]


@mark.parametrize(
    "add_pkgbases, add_dependencies, dependency_state, dumps_raises, return_value",
    [
        (True, False, ActionStateEnum.SUCCESS, False, ActionStateEnum.SUCCESS_TASK),
        (True, False, ActionStateEnum.SUCCESS, True, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.SUCCESS, False, ActionStateEnum.SUCCESS_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, ActionStateEnum.FAILED_TASK),
        (True, False, ActionStateEnum.FAILED_TASK, False, ActionStateEnum.SUCCESS_TASK),
        (True, False, ActionStateEnum.FAILED_TASK, True, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.FAILED_TASK, False, ActionStateEnum.FAILED_DEPENDENCY),
        (False, True, ActionStateEnum.FAILED_TASK, True, ActionStateEnum.FAILED_DEPENDENCY),
    ],
)
def test_writeoutputpackagebasestotmpfileindirtask_do(
    add_pkgbases: bool,
    add_dependencies: bool,
    dependency_state: ActionStateEnum,
    dumps_raises: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [
        Mock(),
        Mock(
            spec=task.CreateOutputPackageBasesTask,
            pkgbases=[outputpackagebasev1],
            state=dependency_state,
        ),
        Mock(),
    ]
    task_ = task.WriteOutputPackageBasesToTmpFileInDirTask(
        directory=tmp_path,
        pkgbases=[outputpackagebasev1] if add_pkgbases else None,
        dependencies=dependencies if add_dependencies else None,
    )
    if dumps_raises:
        with patch("repod.action.task.dumps", side_effect=JSONEncodeError):
            assert task_.do() == return_value
    else:
        assert task_.do() == return_value
        if return_value == ActionStateEnum.SUCCESS_TASK:
            assert task_.filenames[0] == Path(f"{outputpackagebasev1.base}.json.tmp")  # type: ignore[attr-defined]
            assert (tmp_path / task_.filenames[0]).exists()
        else:
            assert task_.filenames == []


@mark.parametrize(
    "add_dependencies, do, remove_file, return_value",
    [
        (False, True, False, ActionStateEnum.NOT_STARTED),
        (False, False, False, ActionStateEnum.NOT_STARTED),
        (False, True, True, ActionStateEnum.NOT_STARTED),
        (True, True, False, ActionStateEnum.NOT_STARTED),
        (True, False, False, ActionStateEnum.NOT_STARTED),
        (True, True, True, ActionStateEnum.NOT_STARTED),
    ],
)
def test_writeoutputpackagebasestotmpfileindirtask_undo(
    add_dependencies: bool,
    do: bool,
    remove_file: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [
        Mock(
            spec=task.CreateOutputPackageBasesTask,
            pkgbases=[outputpackagebasev1],
            state=ActionStateEnum.SUCCESS,
            undo=Mock(return_value=ActionStateEnum.NOT_STARTED),
        ),
    ]
    task_ = task.WriteOutputPackageBasesToTmpFileInDirTask(
        directory=tmp_path,
        pkgbases=[outputpackagebasev1],
        dependencies=dependencies if add_dependencies else None,
    )

    if do:
        task_.do()
        if remove_file:
            for filename in task_.filenames:
                (tmp_path / filename).unlink()

    assert task_.undo() == return_value

    if add_dependencies:
        assert task_.pkgbases == []


@mark.parametrize(
    "add_paths, correct_path_length, add_dependencies, expectation",
    [
        (True, True, False, does_not_raise()),
        (True, False, False, raises(RuntimeError)),
        (False, False, True, does_not_raise()),
        (True, False, True, does_not_raise()),
        (True, True, True, does_not_raise()),
        (False, False, False, raises(RuntimeError)),
    ],
)
def test_movetmpfilestask(
    add_paths: bool,
    correct_path_length: bool,
    add_dependencies: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    source = tmp_path / "foo.tmp"
    destination = tmp_path / "foo"
    destination_backup = tmp_path / "foo.bkp"
    paths = [[source, destination]] if correct_path_length else [[source]]
    source_destination = [
        task.SourceDestination(
            source=source,
            destination=destination,
            destination_backup=destination_backup,
            backup_done=False,
        )
    ]

    dependencies = [
        Mock(),
        Mock(
            spec=task.WriteOutputPackageBasesToTmpFileInDirTask,
        ),
        Mock(),
    ]

    with expectation:
        task_ = task.MoveTmpFilesTask(
            paths=paths if add_paths else None,
            dependencies=dependencies if add_dependencies else None,
        )

    if add_paths and correct_path_length and not add_dependencies:
        assert task_.paths == source_destination
    if add_dependencies:
        assert task_.paths == []


@mark.parametrize(
    (
        "add_paths, add_dependencies, dependency_state, dependency_absolute, destination_exists, "
        "copy2_raises, rename_raises, return_value"
    ),
    [
        (True, False, None, True, True, False, False, ActionStateEnum.SUCCESS_TASK),
        (True, False, None, True, True, True, False, ActionStateEnum.FAILED_TASK),
        (True, False, None, True, True, False, True, ActionStateEnum.FAILED_TASK),
        (True, False, None, True, False, False, False, ActionStateEnum.SUCCESS_TASK),
        (True, False, None, True, False, True, False, ActionStateEnum.SUCCESS_TASK),
        (True, False, None, True, False, False, True, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, True, False, False, ActionStateEnum.SUCCESS_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, True, True, False, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, True, False, True, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, False, False, False, ActionStateEnum.SUCCESS_TASK),
        (False, True, ActionStateEnum.SUCCESS, False, False, False, False, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, False, True, False, ActionStateEnum.SUCCESS_TASK),
        (False, True, ActionStateEnum.SUCCESS, True, False, False, True, ActionStateEnum.FAILED_TASK),
        (False, True, ActionStateEnum.FAILED_TASK, True, False, False, False, ActionStateEnum.FAILED_DEPENDENCY),
    ],
)
def test_movetmpfilestask_do(
    add_paths: bool,
    add_dependencies: bool,
    dependency_state: Optional[ActionStateEnum],
    dependency_absolute: bool,
    destination_exists: bool,
    copy2_raises: bool,
    rename_raises: bool,
    return_value: ActionStateEnum,
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    filename_source = Path("foo.tmp")
    source = tmp_path / filename_source
    source.touch()
    filename_destination = Path("foo")
    destination = tmp_path / filename_destination
    if destination_exists:
        destination.touch()
    paths = [[source, destination]]

    dependencies = [
        Mock(),
        Mock(
            spec=task.WriteOutputPackageBasesToTmpFileInDirTask,
            state=dependency_state,
            directory=tmp_path if dependency_absolute else Path("bar"),
            filenames=[filename_source],
        ),
        Mock(),
    ]

    task_ = task.MoveTmpFilesTask(
        paths=paths if add_paths else None,
        dependencies=dependencies if add_dependencies else None,
    )

    match (destination_exists, copy2_raises, rename_raises):
        case (True, False, False):
            assert task_.do() == return_value
            assert not task_.paths[0].source.exists()
            assert task_.paths[0].destination.exists()
            assert task_.paths[0].destination_backup.exists()
            assert task_.paths[0].backup_done
        case (True, True, False):
            with patch("repod.action.task.copy2", side_effect=Exception("ERROR")):
                assert task_.do() == return_value
            assert task_.paths[0].source.exists()
            assert task_.paths[0].destination.exists()
            assert not task_.paths[0].destination_backup.exists()
            assert not task_.paths[0].backup_done
        case (True, False, True):
            with patch("repod.action.task.Path.rename", side_effect=Exception("ERROR")):
                assert task_.do() == return_value
            assert task_.paths[0].source.exists()
            assert task_.paths[0].destination.exists()
            assert task_.paths[0].destination_backup.exists()
            assert task_.paths[0].backup_done
        case (False, False, False):
            assert task_.do() == return_value
            if task_.state == ActionStateEnum.SUCCESS:
                assert not task_.paths[0].source.exists()
                assert task_.paths[0].destination.exists()
                assert not task_.paths[0].destination_backup.exists()
                assert not task_.paths[0].backup_done
        case (False, True, False):
            with patch("repod.action.task.copy2", side_effect=Exception("ERROR")):
                assert task_.do() == return_value
            assert not task_.paths[0].source.exists()
            assert task_.paths[0].destination.exists()
            assert not task_.paths[0].destination_backup.exists()
            assert not task_.paths[0].backup_done
        case (False, False, True):
            with patch("repod.action.task.Path.rename", side_effect=Exception("ERROR")):
                assert task_.do() == return_value
            assert task_.paths[0].source.exists()
            assert not task_.paths[0].destination.exists()
            assert not task_.paths[0].destination_backup.exists()
            assert not task_.paths[0].backup_done


@mark.parametrize(
    "do, destination_exists, copy2_raises, rename_raises, remove_backup, return_value",
    [
        (False, False, False, False, False, ActionStateEnum.NOT_STARTED),
        (True, True, False, False, False, ActionStateEnum.NOT_STARTED),
        (True, False, False, False, False, ActionStateEnum.NOT_STARTED),
        (True, False, True, False, False, ActionStateEnum.NOT_STARTED),
        (True, False, False, True, False, ActionStateEnum.NOT_STARTED),
        (True, True, False, True, False, ActionStateEnum.NOT_STARTED),
        (True, True, False, False, True, ActionStateEnum.FAILED_UNDO_TASK),
    ],
)
def test_movetmpfilestask_undo(
    do: bool,
    destination_exists: bool,
    copy2_raises: bool,
    rename_raises: bool,
    remove_backup: bool,
    return_value: ActionStateEnum,
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    source = tmp_path / "foo.tmp"
    source.touch()
    destination = tmp_path / "foo"
    if destination_exists:
        destination.touch()

    task_ = task.MoveTmpFilesTask(paths=[[source, destination]])

    if do:
        if copy2_raises:
            with patch("repod.action.task.copy2", side_effect=Exception("ERROR")):
                task_.do()
        elif rename_raises:
            with patch("repod.action.task.Path.rename", side_effect=Exception("ERROR")):
                task_.do()
        else:
            task_.do()

    if remove_backup:
        task_.paths[0].destination_backup.unlink()

    assert task_.undo() == return_value


@mark.parametrize(
    "file_type, add_dependencies",
    [
        (RepoFileEnum.PACKAGE, False),
        (RepoFileEnum.PACKAGE_SIGNATURE, False),
        (RepoFileEnum.PACKAGE, True),
        (RepoFileEnum.PACKAGE_SIGNATURE, True),
    ],
)
def test_filestorepodirtask(
    file_type: RepoFileEnum,
    add_dependencies: bool,
    default_package_file: Tuple[Path, ...],
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    dependencies = [Mock()]
    file = default_package_file[0] if file_type == RepoFileEnum.PACKAGE else default_package_file[1]

    task_ = task.FilesToRepoDirTask(
        files=[file],
        file_type=file_type,
        settings=usersettings,
        name=DEFAULT_NAME,
        architecture=DEFAULT_ARCHITECTURE,
        debug_repo=False,
        staging_repo=False,
        testing_repo=False,
        dependencies=dependencies if add_dependencies else None,
    )

    assert task_.files == [file]
    assert task_.repo_files == []

    if add_dependencies:
        assert task_.dependencies == dependencies


@mark.parametrize(
    "file_type, get_repo_path_raises, repofile_copy_from_raises, return_value",
    [
        (RepoFileEnum.PACKAGE, False, False, ActionStateEnum.SUCCESS_TASK),
        (RepoFileEnum.PACKAGE_SIGNATURE, False, False, ActionStateEnum.SUCCESS_TASK),
        (RepoFileEnum.PACKAGE, True, False, ActionStateEnum.FAILED_TASK),
        ("foo", False, False, ActionStateEnum.FAILED_TASK),
        (RepoFileEnum.PACKAGE, False, True, ActionStateEnum.FAILED_TASK),
        (RepoFileEnum.PACKAGE_SIGNATURE, True, False, ActionStateEnum.FAILED_TASK),
        ("foo", False, False, ActionStateEnum.FAILED_TASK),
        (RepoFileEnum.PACKAGE_SIGNATURE, False, True, ActionStateEnum.FAILED_TASK),
    ],
)
def test_filestorepodirtask_do(
    file_type: RepoFileEnum,
    get_repo_path_raises: bool,
    repofile_copy_from_raises: bool,
    return_value: ActionStateEnum,
    default_package_file: Tuple[Path, ...],
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    file = default_package_file[0] if file_type == RepoFileEnum.PACKAGE else default_package_file[1]

    task_ = task.FilesToRepoDirTask(
        files=[file],
        file_type=file_type,
        settings=usersettings,
        name=Path(DEFAULT_NAME),
        architecture=DEFAULT_ARCHITECTURE,
        debug_repo=False,
        staging_repo=False,
        testing_repo=False,
    )

    if get_repo_path_raises:
        with patch("repod.action.task.UserSettings.get_repo_path", side_effect=RuntimeError):
            assert task_.do() == return_value
    elif repofile_copy_from_raises:
        with patch("repod.action.task.RepoFile.copy_from", side_effect=RepoManagementFileError):
            assert task_.do() == return_value
    else:
        assert task_.do() == return_value
        if isinstance(file_type, RepoFileEnum):
            assert task_.repo_files[0].file_path.exists()
            assert task_.repo_files[0].symlink_path.exists()


@mark.parametrize(
    "file_type, do",
    [
        (RepoFileEnum.PACKAGE, True),
        (RepoFileEnum.PACKAGE, False),
        (RepoFileEnum.PACKAGE_SIGNATURE, True),
        (RepoFileEnum.PACKAGE_SIGNATURE, False),
    ],
)
def test_filestorepodirtask_undo(
    file_type: RepoFileEnum,
    do: bool,
    default_package_file: Tuple[Path, ...],
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    files_to_check: List[Path] = []

    file = default_package_file[0] if file_type == RepoFileEnum.PACKAGE else default_package_file[1]

    task_ = task.FilesToRepoDirTask(
        files=[file],
        file_type=file_type,
        settings=usersettings,
        name=Path(DEFAULT_NAME),
        architecture=DEFAULT_ARCHITECTURE,
        debug_repo=False,
        staging_repo=False,
        testing_repo=False,
    )

    if do:
        assert task_.do() == ActionStateEnum.SUCCESS_TASK
        assert task_.repo_files[0].file_path.exists()
        files_to_check.append(task_.repo_files[0].file_path)
        assert task_.repo_files[0].symlink_path.exists()
        files_to_check.append(task_.repo_files[0].symlink_path)

    assert task_.undo() == ActionStateEnum.NOT_STARTED
    for path in files_to_check:
        assert not path.exists()


def test_addtorepotask() -> None:

    assert task.AddToRepoTask(dependencies=[])


def test_addtorepotask_do() -> None:

    assert task.AddToRepoTask(dependencies=[]).do() == ActionStateEnum.SUCCESS_TASK


def test_addtorepotask_undo() -> None:

    task_ = task.AddToRepoTask(dependencies=[])
    assert task_.do() == ActionStateEnum.SUCCESS_TASK
    assert task_.undo() == ActionStateEnum.NOT_STARTED
