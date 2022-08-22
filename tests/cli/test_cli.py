from argparse import ArgumentTypeError, Namespace
from contextlib import nullcontext as does_not_raise
from logging import DEBUG
from pathlib import Path
from random import sample
from re import Match, fullmatch
from tempfile import TemporaryDirectory
from typing import ContextManager, Optional, Tuple
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark, raises

from repod import commands
from repod.cli import cli
from repod.common.enums import (
    ArchitectureEnum,
    FilesVersionEnum,
    PackageDescVersionEnum,
    PkgVerificationTypeEnum,
    tar_compression_types_for_filename_regex,
)
from repod.config import UserSettings
from repod.config.defaults import DEFAULT_DATABASE_COMPRESSION


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
        (Namespace(package="foo"), raises(RuntimeError)),
    ],
)
def test_repod_file_package(
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    debug_package_file: Tuple[Path, ...],
    tmp_path: Path,
    args: Namespace,
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    settings_mock = Mock()
    args.file = [default_package_file[0]]

    with expectation:
        cli.repod_file_package(args=args, settings=settings_mock)


@mark.parametrize(
    "args, expectation",
    [
        (
            Namespace(repo="importdb", architecture=ArchitectureEnum.ANY, debug=False, staging=False, testing=False),
            does_not_raise(),
        ),
        (
            Namespace(
                repo="writedb",
                architecture=ArchitectureEnum.ANY,
                debug=False,
                staging=False,
                testing=False,
            ),
            does_not_raise(),
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
            does_not_raise(),
        ),
        (Namespace(repo="foo"), raises(RuntimeError)),
    ],
)
@patch("repod.cli.cli.repod_file_repo_importpkg")
def test_repod_file_repo(
    repod_file_repo_importpkg_mock: Mock,
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    debug_package_file: Tuple[Path, ...],
    outputpackagebasev1_json_files_in_dir: Path,
    default_sync_db_file: Tuple[Path, Path],
    tmp_path: Path,
    args: Namespace,
    expectation: ContextManager[str],
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

    with expectation:
        cli.repod_file_repo(args=args, settings=settings_mock)
        if args.repo == "importpkg":
            repod_file_repo_importpkg_mock.assert_called_once()


@mark.parametrize(
    "package_verification, package_verifies, debug_pkg, args, expectation",
    [
        (
            None,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=False,
                debug=False,
                staging=False,
                testing=False,
            ),
            does_not_raise(),
        ),
        (
            None,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=False,
                with_signature=False,
                debug=False,
                staging=False,
                testing=False,
            ),
            does_not_raise(),
        ),
        (
            None,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=False,
                debug=True,
                staging=False,
                testing=False,
            ),
            raises(RuntimeError),
        ),
        (
            None,
            True,
            True,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=False,
                debug=False,
                staging=False,
                testing=False,
            ),
            raises(RuntimeError),
        ),
        (
            None,
            True,
            True,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=False,
                debug=True,
                staging=False,
                testing=False,
            ),
            does_not_raise(),
        ),
        (
            None,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=False,
                with_signature=False,
                debug=True,
                staging=False,
                testing=False,
            ),
            raises(RuntimeError),
        ),
        (
            PkgVerificationTypeEnum.PACMANKEY,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=True,
                debug=False,
                staging=False,
                testing=False,
            ),
            does_not_raise(),
        ),
        (
            PkgVerificationTypeEnum.PACMANKEY,
            False,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=True,
                debug=False,
                staging=False,
                testing=False,
            ),
            raises(RuntimeError),
        ),
        (
            None,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=False,
                with_signature=True,
                debug=False,
                staging=False,
                testing=False,
            ),
            does_not_raise(),
        ),
        (
            None,
            True,
            False,
            Namespace(
                repo="importpkg",
                architecture=ArchitectureEnum.ANY,
                dry_run=True,
                with_signature=True,
                debug=True,
                staging=False,
                testing=False,
            ),
            raises(RuntimeError),
        ),
    ],
)
def test_repod_file_repo_importpkg(
    caplog: LogCaptureFixture,
    default_package_file: Tuple[Path, ...],
    debug_package_file: Tuple[Path, ...],
    outputpackagebasev1_json_files_in_dir: Path,
    default_sync_db_file: Tuple[Path, Path],
    tmp_path: Path,
    usersettings: UserSettings,
    package_verification: Optional[PkgVerificationTypeEnum],
    package_verifies: bool,
    debug_pkg: bool,
    args: Namespace,
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    usersettings.package_verification = package_verification
    args.file = [debug_package_file[0] if debug_pkg else default_package_file[0]]
    args.name = Path("default")

    with patch("repod.cli.cli.PacmanKeyVerifier", Mock(return_value=Mock(verify=Mock(return_value=package_verifies)))):
        with expectation:
            cli.repod_file_repo_importpkg(args=args, settings=usersettings)


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
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=False, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(
                subcommand="package", config=Path("/foo.conf"), system=False, verbose_mode=False, debug_mode=False
            ),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=True, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=False, debug_mode=True),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="package", config=None, system=False, verbose_mode=True, debug_mode=True),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="repo", config=None, system=False, verbose_mode=False, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="schema", config=None, system=False, verbose_mode=False, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="foo", config=None, system=False, verbose_mode=False, debug_mode=False),
            raises(RuntimeError),
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=False, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=True, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=False, debug_mode=True),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="package", config=None, system=True, verbose_mode=True, debug_mode=True),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="repo", config=None, system=True, verbose_mode=False, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="schema", config=None, system=True, verbose_mode=False, debug_mode=False),
            does_not_raise(),
        ),
        (
            Namespace(subcommand="foo", config=None, system=True, verbose_mode=False, debug_mode=False),
            raises(RuntimeError),
        ),
    ],
)
@patch("repod.cli.cli.repod_file_schema")
@patch("repod.cli.cli.repod_file_repo")
@patch("repod.cli.cli.repod_file_package")
@patch("repod.cli.argparse.ArgumentParser.parse_args")
@patch("repod.cli.cli.SystemSettings")
@patch("repod.cli.cli.UserSettings")
def test_repod_file(
    usersettings_mock: Mock,
    systemsettings_mock: Mock,
    parse_args_mock: Mock,
    repod_file_package_mock: Mock,
    repod_file_repo_mock: Mock,
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
