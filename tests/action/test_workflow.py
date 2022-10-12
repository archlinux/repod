from logging import DEBUG
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark

from repod.action import workflow
from repod.common.enums import ActionStateEnum
from repod.config.settings import UserSettings


@patch("repod.action.workflow.exit")
def test_exit_on_error(exit_mock: Mock) -> None:
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
    caplog.set_level(DEBUG)
    createoutputpackagebasestask_mock.spec = workflow.CreateOutputPackageBasesTask
    printoutputpackagebasestask_mock.spec = workflow.PrintOutputPackageBasesTask
    printoutputpackagebasestask_mock.return_value = Mock(return_value=task_return_value)

    workflow.add_packages_dryrun(
        settings=usersettings,
        files=[],
        repo_name=usersettings.repositories[0].name,
        repo_architecture=usersettings.repositories[0].architecture,
        debug_repo=False,
        with_signature=True,
    )

    if task_return_value != ActionStateEnum.SUCCESS:
        exit_on_error_mock.assert_called_once()


@mark.parametrize(
    "with_signature, task_return_value",
    [
        (True, ActionStateEnum.FAILED),
        (True, ActionStateEnum.SUCCESS),
        (False, ActionStateEnum.FAILED),
        (False, ActionStateEnum.SUCCESS),
    ],
)
@patch("repod.action.workflow.exit_on_error")
@patch("repod.action.workflow.AddToRepoTask")
@patch("repod.action.workflow.CreateOutputPackageBasesTask")
@patch("repod.action.workflow.ConsolidateOutputPackageBasesTask")
@patch("repod.action.workflow.WriteOutputPackageBasesToTmpFileInDirTask")
@patch("repod.action.workflow.MoveTmpFilesTask")
@patch("repod.action.workflow.FilesToRepoDirTask")
@patch("repod.action.workflow.WriteSyncDbsToTmpFilesInDirTask")
@patch("repod.action.workflow.RemoveBackupFilesTask")
def test_add_packages(
    removebackupfilestask_mock: Mock,
    writesyncdbstotmpfilesindirtask_mock: Mock,
    filestorepodirtask_mock: Mock,
    movetmpfilestask_mock: Mock,
    writeoutputpackagebasestotmpfileindirtask_mock: Mock,
    consolidateoutputpackagebasestask_mock: Mock,
    createoutputpackagebasestask_mock: Mock,
    addtorepotask_mock: Mock,
    exit_on_error_mock: Mock,
    with_signature: bool,
    task_return_value: ActionStateEnum,
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    removebackupfilestask_mock.spec = workflow.RemoveBackupFilesTask
    writesyncdbstotmpfilesindirtask_mock.spec = workflow.WriteSyncDbsToTmpFilesInDirTask
    filestorepodirtask_mock.spec = workflow.FilesToRepoDirTask
    movetmpfilestask_mock.spec = workflow.MoveTmpFilesTask
    writeoutputpackagebasestotmpfileindirtask_mock.spec = workflow.WriteOutputPackageBasesToTmpFileInDirTask
    consolidateoutputpackagebasestask_mock.spec = workflow.ConsolidateOutputPackageBasesTask
    createoutputpackagebasestask_mock.spec = workflow.CreateOutputPackageBasesTask
    addtorepotask_mock.spec = workflow.AddToRepoTask
    addtorepotask_mock.return_value = Mock(return_value=task_return_value)
    (addtorepotask_mock.return_value).dependencies = []

    workflow.add_packages(
        settings=usersettings,
        files=[],
        repo_name=usersettings.repositories[0].name,
        repo_architecture=usersettings.repositories[0].architecture,
        debug_repo=False,
        staging_repo=False,
        testing_repo=False,
        with_signature=with_signature,
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
