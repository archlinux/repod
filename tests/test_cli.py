from argparse import ArgumentTypeError, Namespace
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

from pytest import mark

from repod import cli, commands, errors, models


@mark.parametrize(
    "fail_argparse, fail_dump",
    [
        (False, False),
        (True, False),
        (False, True),
    ],
)
@patch("repod.operations.dump_db_to_json_files")
@patch("repod.argparse.ArgParseFactory")
@patch("repod.cli.exit")
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
        (True, models.RepoDbTypeEnum.FILES, False, False),
        (False, models.RepoDbTypeEnum.DEFAULT, False, False),
        (True, models.RepoDbTypeEnum.FILES, True, False),
        (False, models.RepoDbTypeEnum.DEFAULT, True, False),
        (True, models.RepoDbTypeEnum.FILES, False, True),
        (False, models.RepoDbTypeEnum.DEFAULT, False, True),
    ],
)
@patch("repod.operations.create_db_from_json_files")
@patch("repod.argparse.ArgParseFactory")
@patch("repod.cli.exit")
def test_json2db(
    exit_mock: Mock,
    argparsefactory_mock: Mock,
    create_db_from_json_files_mock: Mock,
    files: bool,
    db_type: models.RepoDbTypeEnum,
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


def transform_databases(db: str, json_dir: Path, default_syncdb: Path, files_syncdb: Path) -> None:
    commands.run_command(
        cmd=["db2json", f"/var/lib/pacman/sync/{db}.files", str(json_dir)],
        debug=True,
        check=True,
    )
    commands.run_command(
        cmd=["json2db", "-f", str(json_dir), str(files_syncdb)],
        debug=True,
        check=True,
    )
    commands.run_command(
        cmd=["json2db", str(json_dir), str(default_syncdb)],
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
        files_syncdb=empty_syncdbs[1],
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
        files_syncdb=empty_syncdbs[1],
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
        files_syncdb=empty_syncdbs[1],
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
        files_syncdb=empty_syncdbs[1],
    )
    list_databases(db_path=Path(empty_syncdbs[0].parent))
