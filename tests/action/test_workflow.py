"""Tests for repod.action.workflow."""
from logging import DEBUG
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark

from repod.action import workflow
from repod.common.enums import ActionStateEnum
from repod.config.settings import UserSettings


@patch("repod.action.workflow.exit")
def test_exit_on_error(exit_mock: Mock) -> None:
    """Tests for repod.action.workflow.exit_on_error."""
    message = "foo"
    workflow.exit_on_error(message=message)
    exit_mock.assert_called_once_with(1)


@mark.parametrize("task_return_value", [(ActionStateEnum.FAILED), (ActionStateEnum.SUCCESS)])
@patch("repod.action.workflow.exit_on_error")
@patch("repod.action.workflow.PrintOutputPackageBasesTask")
@patch("repod.action.workflow.CreateOutputPackageBasesTask")
def test_add_packages_dryrun(
    createoutputpackagebasestask_mock: Mock,
    printoutputpackagebasestask_mock: Mock,
    exit_on_error_mock: Mock,
    task_return_value: ActionStateEnum,
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    """Tests for repod.action.workflow.add_packages_dryrun."""
    caplog.set_level(DEBUG)
    createoutputpackagebasestask_mock.spec = workflow.CreateOutputPackageBasesTask
    printoutputpackagebasestask_mock.spec = workflow.PrintOutputPackageBasesTask
    printoutputpackagebasestask_mock.return_value = Mock(return_value=task_return_value)

    workflow.add_packages_dryrun(
        settings=usersettings,
        files=[],
        repo_name=usersettings.repositories[0].name,
        repo_architecture=usersettings.repositories[0].architecture,  # type: ignore[arg-type]
        debug_repo=False,
        with_signature=True,
        pkgbase_urls=None,
    )

    if task_return_value != ActionStateEnum.SUCCESS:
        exit_on_error_mock.assert_called_once()


@mark.parametrize(
    "build_requirements_exist, with_archiving, with_signature, with_group, task_return_value",
    [
        (True, True, True, True, ActionStateEnum.FAILED),
        (True, True, True, True, ActionStateEnum.SUCCESS),
        (True, True, False, True, ActionStateEnum.FAILED),
        (True, True, False, True, ActionStateEnum.SUCCESS),
        (True, False, True, True, ActionStateEnum.FAILED),
        (True, False, True, True, ActionStateEnum.SUCCESS),
        (True, False, False, True, ActionStateEnum.FAILED),
        (True, False, False, True, ActionStateEnum.SUCCESS),
        (False, False, True, True, ActionStateEnum.FAILED),
        (False, False, True, True, ActionStateEnum.SUCCESS),
        (False, False, False, True, ActionStateEnum.FAILED),
        (False, False, False, True, ActionStateEnum.SUCCESS),
        (True, True, True, False, ActionStateEnum.FAILED),
        (True, True, True, False, ActionStateEnum.SUCCESS),
        (True, True, False, False, ActionStateEnum.FAILED),
        (True, True, False, False, ActionStateEnum.SUCCESS),
        (True, False, True, False, ActionStateEnum.FAILED),
        (True, False, True, False, ActionStateEnum.SUCCESS),
        (True, False, False, False, ActionStateEnum.FAILED),
        (True, False, False, False, ActionStateEnum.SUCCESS),
        (False, False, True, False, ActionStateEnum.FAILED),
        (False, False, True, False, ActionStateEnum.SUCCESS),
        (False, False, False, False, ActionStateEnum.FAILED),
        (False, False, False, False, ActionStateEnum.SUCCESS),
    ],
)
@patch("repod.action.workflow.exit_on_error")
@patch("repod.action.workflow.AddToRepoTask")
@patch("repod.action.workflow.AddToArchiveTask")
@patch("repod.action.workflow.CleanupRepoTask")
@patch("repod.action.workflow.CreateOutputPackageBasesTask")
@patch("repod.action.workflow.ConsolidateOutputPackageBasesTask")
@patch("repod.action.workflow.RepoGroupTask")
@patch("repod.action.workflow.ReproducibleBuildEnvironmentTask")
@patch("repod.action.workflow.WriteOutputPackageBasesToTmpFileInDirTask")
@patch("repod.action.workflow.MoveTmpFilesTask")
@patch("repod.action.workflow.FilesToRepoDirTask")
@patch("repod.action.workflow.WriteSyncDbsToTmpFilesInDirTask")
@patch("repod.action.workflow.RemoveBackupFilesTask")
@patch("repod.action.workflow.RemoveManagementRepoSymlinksTask")
@patch("repod.action.workflow.RemovePackageRepoSymlinksTask")
def test_add_packages(
    removepackagereposymlinkstask_mock: Mock,
    removemanagementreposymlinkstask_mock: Mock,
    removebackupfilestask_mock: Mock,
    writesyncdbstotmpfilesindirtask_mock: Mock,
    filestorepodirtask_mock: Mock,
    movetmpfilestask_mock: Mock,
    writeoutputpackagebasestotmpfileindirtask_mock: Mock,
    reproduciblebuildenvironmenttask_mock: Mock,
    repogrouptask_mock: Mock,
    consolidateoutputpackagebasestask_mock: Mock,
    createoutputpackagebasestask_mock: Mock,
    cleanuprepotask_mock: Mock,
    addtoarchivetask_mock: Mock,
    addtorepotask_mock: Mock,
    exit_on_error_mock: Mock,
    build_requirements_exist: bool,
    with_archiving: bool,
    with_signature: bool,
    with_group: bool,
    task_return_value: ActionStateEnum,
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    """Tests for repod.action.workflow.add_packages."""
    caplog.set_level(DEBUG)

    removepackagereposymlinkstask_mock.spec = workflow.RemovePackageRepoSymlinksTask
    removemanagementreposymlinkstask_mock.spec = workflow.RemoveManagementRepoSymlinksTask
    removebackupfilestask_mock.spec = workflow.RemoveBackupFilesTask
    writesyncdbstotmpfilesindirtask_mock.spec = workflow.WriteSyncDbsToTmpFilesInDirTask
    filestorepodirtask_mock.spec = workflow.FilesToRepoDirTask
    movetmpfilestask_mock.spec = workflow.MoveTmpFilesTask
    writeoutputpackagebasestotmpfileindirtask_mock.spec = workflow.WriteOutputPackageBasesToTmpFileInDirTask
    reproduciblebuildenvironmenttask_mock.spec = workflow.ReproducibleBuildEnvironmentTask
    repogrouptask_mock.spec = workflow.RepoGroupTask
    consolidateoutputpackagebasestask_mock.spec = workflow.ConsolidateOutputPackageBasesTask
    createoutputpackagebasestask_mock.spec = workflow.CreateOutputPackageBasesTask
    cleanuprepotask_mock.spec = workflow.CleanupRepoTask
    addtoarchivetask_mock.spec = workflow.AddToArchiveTask
    addtorepotask_mock.spec = workflow.AddToRepoTask
    addtorepotask_mock.return_value = Mock(return_value=task_return_value)
    (addtorepotask_mock.return_value).dependencies = []

    if not build_requirements_exist:
        usersettings.build_requirements_exist = None
        usersettings.repositories[0].build_requirements_exist = None

    if not with_archiving:
        usersettings.archiving = None
        usersettings.repositories[0].archiving = None

    if with_group:
        usersettings.repositories[0].group = 1

    workflow.add_packages(
        settings=usersettings,
        files=[],
        repo_name=usersettings.repositories[0].name,
        repo_architecture=usersettings.repositories[0].architecture,
        debug_repo=False,
        staging_repo=False,
        testing_repo=False,
        with_signature=with_signature,
        pkgbase_urls=None,
    )

    if task_return_value != ActionStateEnum.SUCCESS:
        exit_on_error_mock.assert_called_once()
    else:
        removebackupfilestask_mock.assert_called_once()


@mark.parametrize("task_return_value", [(ActionStateEnum.SUCCESS), (ActionStateEnum.FAILED)])
@patch("repod.action.workflow.exit_on_error")
@patch("repod.action.workflow.WriteSyncDbsToTmpFilesInDirTask")
@patch("repod.action.workflow.MoveTmpFilesTask")
@patch("repod.action.workflow.RemoveBackupFilesTask")
def test_write_sync_databases(
    removebackupfilestask_mock: Mock,
    movetmpfilestask_mock: Mock,
    writesyncdbstotmpfilesindirtask_mock: Mock,
    exit_on_error_mock: Mock,
    task_return_value: ActionStateEnum,
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    """Tests for repod.action.workflow.write_sync_databases."""
    caplog.set_level(DEBUG)

    writesyncdbstotmpfilesindirtask_mock.spec = workflow.WriteSyncDbsToTmpFilesInDirTask
    movetmpfilestask_mock.spec = workflow.AddToRepoTask
    movetmpfilestask_mock.return_value = Mock(return_value=task_return_value)

    workflow.write_sync_databases(
        settings=usersettings,
        repo_name=usersettings.repositories[0].name,
        repo_architecture=usersettings.repositories[0].architecture,
        debug_repo=False,
        staging_repo=False,
        testing_repo=False,
    )

    if task_return_value != ActionStateEnum.SUCCESS:
        exit_on_error_mock.assert_called_once()
    else:
        removebackupfilestask_mock.assert_called_once()
