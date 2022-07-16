from argparse import ArgumentTypeError, Namespace
from contextlib import nullcontext as does_not_raise
from logging import DEBUG
from pathlib import Path
from typing import ContextManager, List, Tuple
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark, raises

from repod import commands
from repod.cli import cli


@mark.parametrize(
    "args, expectation",
    [
        (
            Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=False, with_signature=False),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=True, mtree=False, pkginfo=False, with_signature=False),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=False, mtree=True, pkginfo=False, with_signature=False),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=True, with_signature=False),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=False, with_signature=True),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=True, mtree=False, pkginfo=False, with_signature=True),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=False, mtree=True, pkginfo=False, with_signature=True),
            does_not_raise(),
        ),
        (
            Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=True, with_signature=True),
            does_not_raise(),
        ),
        (
            Namespace(package="import", dry_run=True, with_signature=False, staging=False, testing=False),
            does_not_raise(),
        ),
        (
            Namespace(package="import", dry_run=False, with_signature=False, staging=False, testing=False),
            does_not_raise(),
        ),
        (
            Namespace(package="import", dry_run=True, with_signature=False, staging=False, testing=False),
            does_not_raise(),
        ),
        (
            Namespace(package="import", dry_run=False, with_signature=False, staging=False, testing=False),
            does_not_raise(),
        ),
        (
            Namespace(package="import", dry_run=True, with_signature=True, staging=False, testing=False),
            does_not_raise(),
        ),
        (
            Namespace(package="import", dry_run=False, with_signature=True, staging=False, testing=False),
            does_not_raise(),
        ),
        (Namespace(package="foo"), raises(RuntimeError)),
    ],
)
def test_repod_file_package(
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    tmp_path: Path,
    args: Namespace,
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    settings_mock = Mock()
    if args.package in ["inspect", "import"]:
        args.file = [default_package_file[0]]
    if args.package == "import":
        settings_mock.get_repo_path = Mock(return_value=tmp_path)
        args.repo = Path("default")

    with expectation:
        cli.repod_file_package(args=args, settings=settings_mock)


@mark.parametrize(
    "args, invalid_db, expectation",
    [
        (Namespace(management="import", staging=False, testing=False), False, does_not_raise()),
        (Namespace(management="export", compression="none", staging=False, testing=False), False, does_not_raise()),
        (Namespace(management="export", compression="bz2", staging=False, testing=False), False, does_not_raise()),
        (Namespace(management="export", compression="gz", staging=False, testing=False), False, does_not_raise()),
        (Namespace(management="export", compression="xz", staging=False, testing=False), False, does_not_raise()),
        (Namespace(management="export", compression="zst", staging=False, testing=False), False, does_not_raise()),
        (Namespace(management="export", compression="none", staging=False, testing=False), True, raises(RuntimeError)),
        (Namespace(management="foo"), False, raises(RuntimeError)),
    ],
)
def test_repod_file_management(
    caplog: LogCaptureFixture,
    outputpackagebasev1_json_files_in_dir: Path,
    default_sync_db_file: Tuple[Path, Path],
    tmp_path: Path,
    args: Namespace,
    invalid_db: bool,
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    settings_mock = Mock()
    settings_mock.get_repo_path = Mock(return_value=tmp_path)

    if args.management == "import":
        args.file = default_sync_db_file[1]
        args.repo = tmp_path
    if args.management == "export":
        if invalid_db:
            args.file = tmp_path / "foo"
        else:
            args.file = tmp_path / "test.db"
        args.repo = outputpackagebasev1_json_files_in_dir

    with expectation:
        cli.repod_file_management(args=args, settings=settings_mock)


@mark.parametrize(
    "args, invalid_db, expectation",
    [
        (Namespace(syncdb="import", compression="none", staging=False, testing=False), False, does_not_raise()),
        (Namespace(syncdb="import", compression="bz2", staging=False, testing=False), False, does_not_raise()),
        (Namespace(syncdb="import", compression="gz", staging=False, testing=False), False, does_not_raise()),
        (Namespace(syncdb="import", compression="xz", staging=False, testing=False), False, does_not_raise()),
        (Namespace(syncdb="import", compression="zst", staging=False, testing=False), False, does_not_raise()),
        (Namespace(syncdb="import", compression="none", staging=False, testing=False), True, raises(RuntimeError)),
        (Namespace(syncdb="export", staging=False, testing=False), False, does_not_raise()),
        (Namespace(syncdb="foo"), False, raises(RuntimeError)),
    ],
)
def test_repod_file_syncdb(
    caplog: LogCaptureFixture,
    outputpackagebasev1_json_files_in_dir: Path,
    default_sync_db_file: Tuple[Path, Path],
    tmp_path: Path,
    args: Namespace,
    invalid_db: bool,
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    settings_mock = Mock()
    settings_mock.get_repo_path = Mock(return_value=tmp_path)

    if args.syncdb == "import":
        if invalid_db:
            args.file = tmp_path / "foo"
        else:
            args.file = tmp_path / "test.db"
        args.repo = outputpackagebasev1_json_files_in_dir
    if args.syncdb == "export":
        args.file = default_sync_db_file[1]
        args.repo = tmp_path

    with expectation:
        cli.repod_file_syncdb(args=args, settings=settings_mock)


@mark.parametrize(
    "args, expectation",
    [(Namespace(schema="export"), does_not_raise()), (Namespace(schema="foo"), raises(RuntimeError))],
)
def test_repod_file_schema(
    args: Namespace,
    expectation: ContextManager[str],
    tmp_path: Path,
) -> None:
    if args.schema == "export":
        args.dir = tmp_path

    with expectation:
        cli.repod_file_schema(args=args)


@mark.parametrize(
    "args, expectation",
    [
        (Namespace(subcommand="package", config=None, system=False, verbose=False, debug=False), does_not_raise()),
        (
            Namespace(subcommand="package", config=Path("/foo.conf"), system=False, verbose=False, debug=False),
            does_not_raise(),
        ),
        (Namespace(subcommand="package", config=None, system=False, verbose=True, debug=False), does_not_raise()),
        (Namespace(subcommand="package", config=None, system=False, verbose=False, debug=True), does_not_raise()),
        (Namespace(subcommand="package", config=None, system=False, verbose=True, debug=True), does_not_raise()),
        (Namespace(subcommand="management", config=None, system=False, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="syncdb", config=None, system=False, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="schema", config=None, system=False, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="foo", config=None, system=False, verbose=False, debug=False), raises(RuntimeError)),
        (Namespace(subcommand="package", config=None, system=True, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="package", config=None, system=True, verbose=True, debug=False), does_not_raise()),
        (Namespace(subcommand="package", config=None, system=True, verbose=False, debug=True), does_not_raise()),
        (Namespace(subcommand="package", config=None, system=True, verbose=True, debug=True), does_not_raise()),
        (Namespace(subcommand="management", config=None, system=True, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="syncdb", config=None, system=True, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="schema", config=None, system=True, verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="foo", config=None, system=True, verbose=False, debug=False), raises(RuntimeError)),
    ],
)
@patch("repod.cli.cli.repod_file_schema")
@patch("repod.cli.cli.repod_file_syncdb")
@patch("repod.cli.cli.repod_file_management")
@patch("repod.cli.cli.repod_file_package")
@patch("repod.cli.argparse.ArgumentParser.parse_args")
@patch("repod.cli.cli.SystemSettings")
@patch("repod.cli.cli.UserSettings")
def test_repod_file(
    usersettings_mock: Mock,
    systemsettings_mock: Mock,
    parse_args_mock: Mock,
    repod_file_package_mock: Mock,
    repod_file_management_mock: Mock,
    repod_file_syncdb_mock: Mock,
    repod_file_schema_mock: Mock,
    args: Namespace,
    expectation: ContextManager[str],
) -> None:
    user_settings = Mock()
    usersettings_mock.return_value = user_settings
    system_settings = Mock()
    systemsettings_mock.return_value = system_settings

    parse_args_mock.return_value = args

    with expectation:
        cli.repod_file()
        match args.subcommand:
            case "package":
                repod_file_package_mock.assert_called_once_with(
                    args=args, settings=system_settings if args.system else user_settings
                )
            case "management":
                repod_file_management_mock.assert_called_once_with(
                    args=args, settings=system_settings if args.system else user_settings
                )
            case "syncdb":
                repod_file_syncdb_mock.assert_called_once_with(
                    args=args, settings=system_settings if args.system else user_settings
                )
            case "schema":
                repod_file_schema_mock.assert_called_once_with(args=args)
        match args.system:
            case True:
                systemsettings_mock.assert_called_once()
            case False:
                usersettings_mock.assert_called_once()


@patch("repod.cli.argparse.ArgumentParser.parse_args")
def test_repod_file_raise_on_argumenterror(parse_args_mock: Mock) -> None:
    parse_args_mock.side_effect = ArgumentTypeError
    with raises(RuntimeError):
        cli.repod_file()


def transform_databases(db: str, default_syncdb: Path, tmp_path: Path) -> None:
    custom_config = f"""
    [[repositories]]

    name = "{tmp_path}/data/repo/foo"
    staging = "{tmp_path}/data/repo/foo-staging"
    testing = "{tmp_path}/data/repo/foo-testing"
    package_pool = "{tmp_path}/data/pool/package/foo"
    source_pool = "{tmp_path}/data/pool/source/foo"

    [repositories.management_repo]
    directory = "{tmp_path}/management/foo"
    """

    conf_dir = tmp_path / "config"
    conf_dir.mkdir()
    config_path = conf_dir / "repod.conf"
    with open(config_path, "w") as file:
        file.write(custom_config)

    commands.run_command(
        cmd=[
            "repod-file",
            "-d",
            "-c",
            f"{config_path}",
            "management",
            "import",
            f"/var/lib/pacman/sync/{db}.files",
            f"{tmp_path}/data/repo/foo/",
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
            "management",
            "export",
            f"{tmp_path}/data/repo/foo/",
            str(default_syncdb),
        ],
        debug=True,
        check=True,
    )


def list_databases(db_path: Path) -> None:
    cache_path = db_path / "cache"
    cache_path.mkdir(parents=True)
    pacman_conf_path = cache_path / "pacman.conf"
    pacman_conf_contents = """[options]
    HoldPkg = pacman glibc
    Architecture = auto
    SigLevel = Required DatabaseOptional
    LocalFileSigLevel = Optional
    [tmp]
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
            str(db_path),
            "-Sl",
            "tmp",
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
            str(db_path),
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
def test_transform_core_databases(empty_dir: Path, empty_syncdbs: List[Path], tmp_path: Path) -> None:
    transform_databases(
        db="core",
        default_syncdb=empty_syncdbs[0],
        tmp_path=tmp_path,
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/extra.files").exists(),
    reason="/var/lib/pacman/sync/extra.files does not exist",
)
def test_transform_extra_databases(empty_dir: Path, empty_syncdbs: List[Path], tmp_path: Path) -> None:
    transform_databases(
        db="extra",
        default_syncdb=empty_syncdbs[0],
        tmp_path=tmp_path,
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/community.files").exists(),
    reason="/var/lib/pacman/sync/community.files does not exist",
)
def test_transform_community_databases(empty_dir: Path, empty_syncdbs: List[Path], tmp_path: Path) -> None:
    transform_databases(
        db="community",
        default_syncdb=empty_syncdbs[0],
        tmp_path=tmp_path,
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/multilib.files").exists(),
    reason="/var/lib/pacman/sync/multilib.files does not exist",
)
def test_transform_multilib_databases(empty_dir: Path, empty_syncdbs: List[Path], tmp_path: Path) -> None:
    transform_databases(
        db="multilib",
        default_syncdb=empty_syncdbs[0],
        tmp_path=tmp_path,
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))
