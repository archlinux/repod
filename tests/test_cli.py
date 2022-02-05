import shutil
import tempfile
from argparse import ArgumentTypeError, Namespace
from pathlib import Path
from typing import Dict, Iterator
from unittest.mock import Mock, patch

from pytest import fixture, mark

from repo_management import cli, commands, defaults, errors


@fixture(scope="function")
def empty_dir() -> Iterator[Path]:
    directory = tempfile.mkdtemp()
    yield Path(directory)
    shutil.rmtree(directory)


@fixture(scope="function")
def empty_file() -> Iterator[Path]:
    [foo, file_name] = tempfile.mkstemp()
    yield Path(file_name)


@mark.parametrize(
    "fail_argparse, fail_dump",
    [
        (False, False),
        (True, False),
        (False, True),
    ],
)
@patch("repo_management.operations.dump_db_to_json_files")
@patch("repo_management.argparse.ArgParseFactory")
@patch("repo_management.cli.exit")
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
        (True, defaults.RepoDbType.FILES, False, False),
        (False, defaults.RepoDbType.DEFAULT, False, False),
        (True, defaults.RepoDbType.FILES, True, False),
        (False, defaults.RepoDbType.DEFAULT, True, False),
        (True, defaults.RepoDbType.FILES, False, True),
        (False, defaults.RepoDbType.DEFAULT, False, True),
    ],
)
@patch("repo_management.operations.create_db_from_json_files")
@patch("repo_management.argparse.ArgParseFactory")
@patch("repo_management.cli.exit")
def test_json2db(
    exit_mock: Mock,
    argparsefactory_mock: Mock,
    create_db_from_json_files_mock: Mock,
    files: bool,
    db_type: defaults.RepoDbType,
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


@mark.integration
@mark.parametrize(
    "db",
    [
        ("core"),
        ("extra"),
        ("community"),
    ],
)
def test_transform_databases(db: str, empty_dir: Path, empty_file: Path) -> None:
    commands.run_command(
        cmd=["db2json", f"/var/lib/pacman/sync/{db}.files", empty_dir.as_posix()],
        debug=True,
        check=True,
    )
    commands.run_command(
        cmd=["json2db", "-f", empty_dir.as_posix(), empty_file.as_posix()],
        debug=True,
        check=True,
    )


@mark.integration
def test_transform_databases_and_use_with_pacman(empty_dir: Path) -> None:
    dbs = ["core", "extra", "community"]
    json_paths: Dict[str, Path] = {}
    pacman_path = empty_dir / "pacman"
    pacman_path.mkdir(parents=True)
    db_path = empty_dir / "pacman/db_path"
    db_path.mkdir(parents=True)
    sync_path = empty_dir / "pacman/db_path/sync"
    sync_path.mkdir(parents=True)
    cache_path = empty_dir / "pacman/cache_path"
    cache_path.mkdir(parents=True)
    for db in dbs:
        json_path = empty_dir / db
        json_path.mkdir()
        json_paths[db] = json_path

    for (name, json_path) in json_paths.items():
        commands.run_command(
            cmd=["db2json", f"/var/lib/pacman/sync/{name}.files", str(json_path)],
            debug=True,
            check=True,
        )
        commands.run_command(
            cmd=["json2db", str(json_path), f"{sync_path}/{name}.db"],
            debug=True,
            check=True,
        )
        commands.run_command(
            cmd=["json2db", "-f", str(json_path), f"{sync_path}/{name}.files"],
            debug=True,
            check=True,
        )

    commands.run_command(
        cmd=[
            "pacman",
            "--cache",
            str(cache_path),
            "--logfile",
            f"{pacman_path}/pacman.log",
            "--dbpath",
            str(db_path),
            "-Ss",
            "linux",
        ],
        debug=True,
        check=True,
    )
    commands.run_command(
        cmd=[
            "pacman",
            "--cache",
            str(cache_path),
            "--logfile",
            f"{pacman_path}/pacman.log",
            "--dbpath",
            str(db_path),
            "-Fl",
            "linux",
        ],
        debug=True,
        check=True,
    )
