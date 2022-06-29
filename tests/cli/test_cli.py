from argparse import ArgumentTypeError, Namespace
from contextlib import nullcontext as does_not_raise
from logging import DEBUG
from pathlib import Path
from typing import ContextManager, List, Tuple
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark, raises

from repod import commands, errors
from repod.cli import cli
from repod.repo.package import RepoDbTypeEnum


@mark.parametrize(
    "args, only_package, dup_package, expectation",
    [
        (Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=False), True, False, does_not_raise()),
        (Namespace(package="inspect", buildinfo=True, mtree=False, pkginfo=False), True, False, does_not_raise()),
        (Namespace(package="inspect", buildinfo=False, mtree=True, pkginfo=False), True, False, does_not_raise()),
        (Namespace(package="inspect", buildinfo=False, mtree=False, pkginfo=True), True, False, does_not_raise()),
        (Namespace(package="import", dry_run=True), True, False, does_not_raise()),
        (Namespace(package="import", dry_run=False), True, False, does_not_raise()),
        (Namespace(package="import", dry_run=True), False, False, does_not_raise()),
        (Namespace(package="import", dry_run=False), False, False, does_not_raise()),
        (Namespace(package="import", dry_run=True), False, True, raises(RuntimeError)),
        (Namespace(package="import", dry_run=False), False, True, raises(RuntimeError)),
        (Namespace(package="foo"), True, False, raises(RuntimeError)),
    ],
)
def test_repod_file_package(
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    tmp_path: Path,
    args: Namespace,
    only_package: bool,
    dup_package: bool,
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    if args.package in ["inspect", "import"]:
        if only_package:
            args.file = [default_package_file[0]]
        else:
            args.file = [default_package_file[0], default_package_file[1]]
        if dup_package:
            args.file += [default_package_file[0]]
    if args.package == "import":
        args.repo = tmp_path

    with expectation:
        cli.repod_file_package(args=args)


@mark.parametrize(
    "args, invalid_db, expectation",
    [
        (Namespace(management="import"), False, does_not_raise()),
        (Namespace(management="export", compression="none"), False, does_not_raise()),
        (Namespace(management="export", compression="bz2"), False, does_not_raise()),
        (Namespace(management="export", compression="gz"), False, does_not_raise()),
        (Namespace(management="export", compression="xz"), False, does_not_raise()),
        (Namespace(management="export", compression="zst"), False, does_not_raise()),
        (Namespace(management="export", compression="none"), True, raises(RuntimeError)),
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
        cli.repod_file_management(args=args)


@mark.parametrize(
    "args, invalid_db, expectation",
    [
        (Namespace(syncdb="import", compression="none"), False, does_not_raise()),
        (Namespace(syncdb="import", compression="bz2"), False, does_not_raise()),
        (Namespace(syncdb="import", compression="gz"), False, does_not_raise()),
        (Namespace(syncdb="import", compression="xz"), False, does_not_raise()),
        (Namespace(syncdb="import", compression="zst"), False, does_not_raise()),
        (Namespace(syncdb="import", compression="none"), True, raises(RuntimeError)),
        (Namespace(syncdb="export"), False, does_not_raise()),
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
        cli.repod_file_syncdb(args=args)


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
        (Namespace(subcommand="package", verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="package", verbose=True, debug=False), does_not_raise()),
        (Namespace(subcommand="package", verbose=False, debug=True), does_not_raise()),
        (Namespace(subcommand="package", verbose=True, debug=True), does_not_raise()),
        (Namespace(subcommand="management", verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="syncdb", verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="schema", verbose=False, debug=False), does_not_raise()),
        (Namespace(subcommand="foo", verbose=False, debug=False), raises(RuntimeError)),
    ],
)
@patch("repod.cli.cli.repod_file_schema")
@patch("repod.cli.cli.repod_file_syncdb")
@patch("repod.cli.cli.repod_file_management")
@patch("repod.cli.cli.repod_file_package")
@patch("repod.cli.argparse.ArgumentParser.parse_args")
def test_repod_file(
    parse_args_mock: Mock,
    repod_file_package_mock: Mock,
    repod_file_management_mock: Mock,
    repod_file_syncdb_mock: Mock,
    repod_file_schema_mock: Mock,
    args: Namespace,
    expectation: ContextManager[str],
) -> None:
    parse_args_mock.return_value = args

    with expectation:
        cli.repod_file()
        match args.subcommand:
            case "package":
                repod_file_package_mock.assert_called_once_with(args=args)
            case "management":
                repod_file_management_mock.assert_called_once_with(args=args)
            case "syncdb":
                repod_file_syncdb_mock.assert_called_once_with(args=args)
            case "schema":
                repod_file_schema_mock.assert_called_once_with(args=args)


@patch("repod.cli.argparse.ArgumentParser.parse_args")
def test_repod_file_raise_on_argumenterror(parse_args_mock: Mock) -> None:
    parse_args_mock.side_effect = ArgumentTypeError
    with raises(RuntimeError):
        cli.repod_file()


@mark.parametrize(
    "fail_argparse, fail_dump",
    [
        (False, False),
        (True, False),
        (False, True),
    ],
)
@patch("repod.operations.dump_db_to_json_files")
@patch("repod.cli.argparse.ArgParseFactory")
@patch("repod.cli.cli.exit")
def test_db2json(
    exit_mock: Mock,
    argparsefactory_mock: Mock,
    dump_db_to_json_files_mock: Mock,
    fail_argparse: bool,
    fail_dump: bool,
) -> None:
    namespace = Namespace(db_file="db_file", output_dir="output_dir")
    if fail_argparse:
        argparsefactory_mock.db2json.side_effect = ArgumentTypeError
    else:
        argparsefactory_mock.db2json.return_value = Mock(parse_args=Mock(return_value=namespace))
    if fail_dump:
        dump_db_to_json_files_mock.side_effect = errors.RepoManagementError

    cli.db2json()
    if fail_argparse or fail_dump:
        exit_mock.assert_called_once_with(1)
    else:
        dump_db_to_json_files_mock.assert_called_once_with(
            input_path=namespace.db_file,
            output_path=namespace.output_dir,
        )


@mark.parametrize(
    "files, db_type, fail_argparse, fail_create",
    [
        (True, RepoDbTypeEnum.FILES, False, False),
        (False, RepoDbTypeEnum.DEFAULT, False, False),
        (True, RepoDbTypeEnum.FILES, True, False),
        (False, RepoDbTypeEnum.DEFAULT, True, False),
        (True, RepoDbTypeEnum.FILES, False, True),
        (False, RepoDbTypeEnum.DEFAULT, False, True),
    ],
)
@patch("repod.operations.create_db_from_json_files")
@patch("repod.cli.argparse.ArgParseFactory")
@patch("repod.cli.cli.exit")
def test_json2db(
    exit_mock: Mock,
    argparsefactory_mock: Mock,
    create_db_from_json_files_mock: Mock,
    files: bool,
    db_type: RepoDbTypeEnum,
    fail_argparse: bool,
    fail_create: bool,
) -> None:
    namespace = Namespace(db_file="db_file", input_dir="input_dir", files=files)
    if fail_argparse:
        argparsefactory_mock.json2db.side_effect = ArgumentTypeError
    else:
        argparsefactory_mock.json2db.return_value = Mock(parse_args=Mock(return_value=namespace))
    if fail_create:
        create_db_from_json_files_mock.side_effect = errors.RepoManagementError

    cli.json2db()
    if fail_argparse:
        exit_mock.assert_called_once_with(1)
    if fail_create:
        create_db_from_json_files_mock.assert_called_once_with(
            input_path=namespace.input_dir,
            output_path=namespace.db_file,
            db_type=db_type,
        )
        exit_mock.assert_called_once_with(1)
    if not fail_argparse and not fail_create:
        create_db_from_json_files_mock.assert_called_once_with(
            input_path=namespace.input_dir,
            output_path=namespace.db_file,
            db_type=db_type,
        )


def transform_databases(db: str, json_dir: Path, default_syncdb: Path) -> None:
    commands.run_command(
        cmd=["repod-file", "management", "import", f"/var/lib/pacman/sync/{db}.files", str(json_dir)],
        debug=True,
        check=True,
    )
    commands.run_command(
        cmd=["repod-file", "management", "export", str(json_dir), str(default_syncdb)],
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
def test_transform_core_databases(empty_dir: Path, empty_syncdbs: List[Path]) -> None:
    transform_databases(
        db="core",
        json_dir=empty_dir,
        default_syncdb=empty_syncdbs[0],
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/extra.files").exists(),
    reason="/var/lib/pacman/sync/extra.files does not exist",
)
def test_transform_extra_databases(empty_dir: Path, empty_syncdbs: List[Path]) -> None:
    transform_databases(
        db="extra",
        json_dir=empty_dir,
        default_syncdb=empty_syncdbs[0],
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/community.files").exists(),
    reason="/var/lib/pacman/sync/community.files does not exist",
)
def test_transform_community_databases(empty_dir: Path, empty_syncdbs: List[Path]) -> None:
    transform_databases(
        db="community",
        json_dir=empty_dir,
        default_syncdb=empty_syncdbs[0],
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))


@mark.integration
@mark.skipif(
    not Path("/var/lib/pacman/sync/multilib.files").exists(),
    reason="/var/lib/pacman/sync/multilib.files does not exist",
)
def test_transform_multilib_databases(empty_dir: Path, empty_syncdbs: List[Path]) -> None:
    transform_databases(
        db="multilib",
        json_dir=empty_dir,
        default_syncdb=empty_syncdbs[0],
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))
