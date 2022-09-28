from argparse import ArgumentParser, ArgumentTypeError, Namespace
from logging import DEBUG
from pathlib import Path
from random import sample
from re import Match, fullmatch
from tempfile import TemporaryDirectory
from typing import Optional, Tuple
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark, raises

from repod import commands
from repod.action.task import (
    AddToRepoTask,
    MoveTmpFilesTask,
    PrintOutputPackageBasesTask,
)
from repod.cli import cli
from repod.common.enums import (
    ActionStateEnum,
    ArchitectureEnum,
    FilesVersionEnum,
    PackageDescVersionEnum,
    tar_compression_types_for_filename_regex,
)
from repod.config import UserSettings
from repod.config.defaults import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_DATABASE_COMPRESSION,
    DEFAULT_NAME,
)


@mark.parametrize(
    "message, argparser",
    [
        ("foo", None),
        ("foo", ArgumentParser()),
    ],
)
@patch("repod.cli.cli.exit")
def test_exit_on_error(exit_mock: Mock, message: str, argparser: Optional[ArgumentParser]) -> None:
    cli.exit_on_error(message=message, argparser=argparser)
    exit_mock.assert_called_once_with(1)


@mark.parametrize(
    "args, calls_exit_on_error",
    [
        (Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=False, with_signature=False), False),
        (Namespace(package="inspect", buildinfo=True, mtree=False, pkginfo=False, with_signature=False), False),
        (Namespace(package="inspect", buildinfo=False, mtree=True, pkginfo=False, with_signature=False), False),
        (Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=True, with_signature=False), False),
        (Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=False, with_signature=True), False),
        (Namespace(package="inspect", buildinfo=True, mtree=False, pkginfo=False, with_signature=True), False),
        (Namespace(package="inspect", buildinfo=False, mtree=True, pkginfo=False, with_signature=True), False),
        (Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=True, with_signature=True), False),
        (Namespace(package="foo"), True),
    ],
)
@patch("repod.cli.cli.exit_on_error")
def test_repod_file_package(
    exit_on_error_mock: Mock,
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    tmp_path: Path,
    args: Namespace,
    calls_exit_on_error: bool,
) -> None:
    caplog.set_level(DEBUG)

    settings_mock = Mock()
    args.file = [default_package_file[0]]

    cli.repod_file_package(args=args, settings=settings_mock)
    if calls_exit_on_error:
        exit_on_error_mock.assert_called_once()


@mark.parametrize(
    "args, calls_exit_on_error",
    [
        (
            Namespace(repo="importdb", architecture=ArchitectureEnum.ANY, debug=False, staging=False, testing=False),
            False,
        ),
        (
            Namespace(
                repo="writedb",
                architecture=ArchitectureEnum.ANY,
                debug=False,
                staging=False,
                testing=False,
            ),
            False,
        ),
        (
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=False,
                debug=False,
                staging=False,
                testing=False,
            ),
            False,
        ),
        (Namespace(repo="foo"), True),
    ],
)
@patch("repod.cli.cli.repod_file_repo_importpkg")
@patch("repod.cli.cli.exit_on_error")
def test_repod_file_repo(
    exit_on_error_mock: Mock,
    repod_file_repo_importpkg_mock: Mock,
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    outputpackagebasev1_json_files_in_dir: Path,
    default_sync_db_file: Tuple[Path, Path],
    tmp_path: Path,
    args: Namespace,
    calls_exit_on_error: bool,
) -> None:
    caplog.set_level(DEBUG)

    settings_mock = Mock()
    settings_mock.get_repo_path = Mock(return_value=tmp_path)
    settings_mock.get_repo_database_compression = Mock(return_value=DEFAULT_DATABASE_COMPRESSION)
    syncdb_settings_mock = Mock()
    syncdb_settings_mock.desc_version = PackageDescVersionEnum.DEFAULT
    syncdb_settings_mock.files_version = FilesVersionEnum.DEFAULT
    settings_mock.syncdb_settings = syncdb_settings_mock

    if args.repo == "importdb":
        args.file = default_sync_db_file[1]
        args.name = tmp_path
    if args.repo == "writedb":
        args.name = "default"

    cli.repod_file_repo(args=args, settings=settings_mock)
    if args.repo == "importpkg":
        repod_file_repo_importpkg_mock.assert_called_once()
    if calls_exit_on_error:
        exit_on_error_mock.assert_called_once()


@mark.parametrize(
    "print_outputpackagebases_task_return",
    [
        (ActionStateEnum.SUCCESS),
        (ActionStateEnum.FAILED),
    ],
)
@patch("repod.cli.cli.exit_on_error")
def test_repod_file_repo_importpkg_dryrun(
    exit_on_error_mock: Mock,
    print_outputpackagebases_task_return: ActionStateEnum,
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    print_outputpackagebases_task_mock = Mock(
        spec=PrintOutputPackageBasesTask,
        return_value=Mock(return_value=print_outputpackagebases_task_return),
    )

    with patch("repod.cli.cli.PrintOutputPackageBasesTask", return_value=print_outputpackagebases_task_mock):
        cli.repod_file_repo_importpkg(
            args=Namespace(
                dry_run=True,
                with_signature=True,
                architecture=None,
                name=usersettings.repositories[0].name,
                pretty=True,
                debug=False,
                file=[Path("foo")],
            ),
            settings=usersettings,
        )
    print_outputpackagebases_task_mock.assert_called_once()

    if print_outputpackagebases_task_return != ActionStateEnum.SUCCESS:
        exit_on_error_mock.assert_called_once()
        print_outputpackagebases_task_mock.undo.assert_called_once()


@mark.parametrize(
    "with_signature, add_to_repo_task_return",
    [
        (True, ActionStateEnum.SUCCESS),
        (False, ActionStateEnum.SUCCESS),
        (True, ActionStateEnum.FAILED),
        (False, ActionStateEnum.FAILED),
    ],
)
@patch("repod.cli.cli.exit_on_error")
def test_repod_file_repo_importpkg(
    exit_on_error_mock: Mock,
    with_signature: bool,
    add_to_repo_task_return: ActionStateEnum,
    usersettings: UserSettings,
    caplog: LogCaptureFixture,
    tmp_path: Path,
) -> None:
    caplog.set_level(DEBUG)

    tmp_file = tmp_path / "foo.tmp"
    file = tmp_path / "foo"
    backup_file = tmp_path / "foo.bkp"
    backup_file.touch()
    movetmpfiles_task = MoveTmpFilesTask(paths=[[tmp_file, file]])
    movetmpfiles_task.state = ActionStateEnum.SUCCESS

    add_to_repo_task_mock = Mock(
        spec=AddToRepoTask,
        return_value=add_to_repo_task_return,
        dependencies=[movetmpfiles_task],
    )

    with patch("repod.cli.cli.AddToRepoTask", return_value=add_to_repo_task_mock):
        cli.repod_file_repo_importpkg(
            args=Namespace(
                architecture=DEFAULT_ARCHITECTURE,
                debug=False,
                dry_run=False,
                file=[Path("foo")],
                name=Path(DEFAULT_NAME),
                pretty=True,
                staging=False,
                testing=False,
                with_signature=with_signature,
            ),
            settings=usersettings,
        )
    add_to_repo_task_mock.assert_called_once()

    if add_to_repo_task_return == ActionStateEnum.SUCCESS:
        assert not backup_file.exists()
    else:
        exit_on_error_mock.assert_called_once()
        add_to_repo_task_mock.undo.assert_called_once()
        assert backup_file.exists()


@mark.parametrize(
    "args, calls_exit_on_error",
    [(Namespace(schema="export"), False), (Namespace(schema="foo"), True)],
)
@patch("repod.cli.cli.exit_on_error")
def test_repod_file_schema(
    exit_on_error_mock: Mock,
    tmp_path: Path,
    args: Namespace,
    calls_exit_on_error: bool,
) -> None:
    if args.schema == "export":
        args.dir = tmp_path

    cli.repod_file_schema(args=args)
    if calls_exit_on_error:
        exit_on_error_mock.assert_called_once()


@mark.parametrize(
    "args, calls_exit_on_error",
    [
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=False, debug_mode=False),
            False,
        ),
        (
            Namespace(
                subcommand="package", config=Path("/foo.conf"), system=False, verbose_mode=False, debug_mode=False
            ),
            False,
        ),
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=True, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=False, debug_mode=True),
            False,
        ),
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=True, debug_mode=True),
            False,
        ),
        (
            Namespace(subcommand="repo", config=None, system=False, verbose_mode=False, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="schema", config=None, system=False, verbose_mode=False, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="foo", config=None, system=False, verbose_mode=False, debug_mode=False),
            True,
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=False, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=True, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=False, debug_mode=True),
            False,
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=True, debug_mode=True),
            False,
        ),
        (
            Namespace(subcommand="repo", config=None, system=True, verbose_mode=False, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="schema", config=None, system=True, verbose_mode=False, debug_mode=False),
            False,
        ),
        (
            Namespace(subcommand="foo", config=None, system=True, verbose_mode=False, debug_mode=False),
            True,
        ),
    ],
)
@patch("repod.cli.cli.repod_file_schema")
@patch("repod.cli.cli.repod_file_repo")
@patch("repod.cli.cli.repod_file_package")
@patch("repod.cli.argparse.ArgumentParser.parse_args")
@patch("repod.cli.cli.SystemSettings")
@patch("repod.cli.cli.UserSettings")
@patch("repod.cli.cli.exit_on_error")
def test_repod_file(
    exit_on_error_mock: Mock,
    usersettings_mock: Mock,
    systemsettings_mock: Mock,
    parse_args_mock: Mock,
    repod_file_package_mock: Mock,
    repod_file_repo_mock: Mock,
    repod_file_schema_mock: Mock,
    args: Namespace,
    calls_exit_on_error: bool,
) -> None:
    user_settings = Mock()
    usersettings_mock.return_value = user_settings
    system_settings = Mock()
    systemsettings_mock.return_value = system_settings

    parse_args_mock.return_value = args

    cli.repod_file()
    match args.subcommand:
        case "package":
            repod_file_package_mock.assert_called_once_with(
                args=args, settings=system_settings if args.system else user_settings
            )
        case "repo":
            repod_file_repo_mock.assert_called_once_with(
                args=args, settings=system_settings if args.system else user_settings
            )
        case "schema":
            repod_file_schema_mock.assert_called_once_with(args=args)
    match args.system:
        case True:
            systemsettings_mock.assert_called_once()
        case False:
            usersettings_mock.assert_called_once()

    if calls_exit_on_error:
        exit_on_error_mock.assert_called_once()


@patch("repod.cli.argparse.ArgumentParser.parse_args")
def test_repod_file_raise_on_argumenterror(parse_args_mock: Mock) -> None:
    parse_args_mock.side_effect = ArgumentTypeError
    with raises(RuntimeError):
        cli.repod_file()


def transform_databases(repo_name: str, base_path: Path) -> None:
    custom_config = f"""
    [[repositories]]

    name = "{base_path}/data/repo/package/{repo_name}"
    debug = "{base_path}/data/repo/package/{repo_name}-debug"
    staging = "{base_path}/data/repo/package/{repo_name}-staging"
    testing = "{base_path}/data/repo/package/{repo_name}-testing"
    package_pool = "{base_path}/data/pool/package/{repo_name}"
    source_pool = "{base_path}/data/pool/source/{repo_name}"

    [repositories.management_repo]
    directory = "{base_path}/management/{repo_name}"
    """

    config_path = base_path / "repod.conf"
    with open(config_path, "w") as file:
        file.write(custom_config)

    commands.run_command(
        cmd=[
            "repod-file",
            "-d",
            "-c",
            f"{config_path}",
            "repo",
            "importdb",
            f"/var/lib/pacman/sync/{repo_name}.files",
            f"{base_path}/data/repo/package/{repo_name}/",
        ],
        debug=True,
        check=True,
    )
    commands.run_command(
        cmd=[
            "repod-file",
            "-d",
            "-c",
            f"{config_path}",
            "repo",
            "writedb",
            f"{base_path}/data/repo/package/{repo_name}/",
        ],
        debug=True,
        check=True,
    )


def list_database(repo_name: str, base_path: Path) -> None:
    syncdb_path = Path(f"{base_path}/data/repo/package/{repo_name}/any/")
    with TemporaryDirectory(prefix="pacman_", dir=base_path) as dbpath:
        (Path(dbpath) / "sync").symlink_to(syncdb_path)
        cache_path = base_path / "cache"
        cache_path.mkdir(parents=True)
        pacman_conf_path = cache_path / "pacman.conf"
        pacman_conf_contents = f"""[options]
        HoldPkg = pacman glibc
        Architecture = auto
        SigLevel = Required DatabaseOptional
        LocalFileSigLevel = Optional
        [{repo_name}]
        Include = /etc/pacman.d/mirrorlist
        """

        with open(pacman_conf_path, "w") as file:
            print(pacman_conf_contents, file=file)

        commands.run_command(
            cmd=[
                "pacman",
                "--config",
                str(pacman_conf_path),
                "--cache",
                str(cache_path),
                "--logfile",
                f"{cache_path}/pacman.log",
                "--dbpath",
                f"{dbpath}",
                "-Sl",
                f"{repo_name}",
            ],
            debug=True,
            check=True,
        )
        commands.run_command(
            cmd=[
                "pacman",
                "--config",
                str(pacman_conf_path),
                "--cache",
                str(cache_path),
                "--logfile",
                f"{cache_path}/pacman.log",
                "--dbpath",
                f"{dbpath}",
                "-Fl",
            ],
            debug=True,
            check=True,
        )


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/core.files").exists(),
    reason="/var/lib/pacman/sync/core.files does not exist",
)
def test_transform_core_databases(empty_dir: Path, tmp_path: Path) -> None:
    name = "core"
    transform_databases(repo_name=name, base_path=tmp_path)
    list_database(repo_name=name, base_path=tmp_path)


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/extra.files").exists(),
    reason="/var/lib/pacman/sync/extra.files does not exist",
)
def test_transform_extra_databases(empty_dir: Path, tmp_path: Path) -> None:
    name = "extra"
    transform_databases(repo_name=name, base_path=tmp_path)
    list_database(repo_name=name, base_path=tmp_path)


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/community.files").exists(),
    reason="/var/lib/pacman/sync/community.files does not exist",
)
def test_transform_community_databases(empty_dir: Path, tmp_path: Path) -> None:
    name = "community"
    transform_databases(repo_name="community", base_path=tmp_path)
    list_database(repo_name=name, base_path=tmp_path)


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/multilib.files").exists(),
    reason="/var/lib/pacman/sync/multilib.files does not exist",
)
def test_transform_multilib_databases(empty_dir: Path, tmp_path: Path) -> None:
    name = "multilib"
    transform_databases(repo_name=name, base_path=tmp_path)
    list_database(repo_name=name, base_path=tmp_path)


@mark.integration
@mark.skipif(
    not Path("/var/cache/pacman/pkg/").exists(),
    reason="Package cache in /var/cache/pacman/pkg/ does not exist",
)
def test_import_into_default_repo(tmp_path: Path) -> None:
    packages = sorted(
        [
            path
            for path in list(Path("/var/cache/pacman/pkg/").iterdir())
            if isinstance(fullmatch(rf"^.*\.pkg\.tar({tar_compression_types_for_filename_regex()})$", str(path)), Match)
        ]
    )
    if len(packages) > 50:
        packages = sample(packages, 50)

    custom_config = f"""
    [[repositories]]

    architecture = "x86_64"
    name = "{tmp_path}/data/repo/package/default/"
    debug = "{tmp_path}/data/repo/package/default-debug/"
    staging = "{tmp_path}/data/repo/package/default-staging/"
    testing = "{tmp_path}/data/repo/package/default-testing/"
    package_pool = "{tmp_path}/data/pool/package/default/"
    source_pool = "{tmp_path}/data/pool/source/default/"

    [repositories.management_repo]
    directory = "{tmp_path}/management/default/"
    """

    config_path = tmp_path / "repod.conf"
    with open(config_path, "w") as file:
        file.write(custom_config)

    for package in packages:
        commands.run_command(
            cmd=[
                "repod-file",
                "-d",
                "-c",
                f"{config_path}",
                "repo",
                "importpkg",
                "-s",
                f"{package}",
                f"{tmp_path}/data/repo/package/default/",
            ],
            debug=True,
            check=True,
        )

    commands.run_command(
        cmd=[
            "repod-file",
            "-d",
            "-c",
            f"{config_path}",
            "repo",
            "writedb",
            f"{tmp_path}/data/repo/package/default/",
        ],
        debug=True,
        check=True,
    )
