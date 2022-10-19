import asyncio
from argparse import ArgumentParser, Namespace
from logging import DEBUG, INFO, WARNING, StreamHandler, debug, getLogger
from pathlib import Path
from sys import exit, stderr, stdout
from unittest.mock import patch

from orjson import dumps

from repod import export_schemas
from repod.action.workflow import (
    add_packages,
    add_packages_dryrun,
    write_sync_databases,
)
from repod.cli import argparse
from repod.common.enums import RepoDirTypeEnum
from repod.config import SystemSettings, UserSettings
from repod.config.defaults import ORJSON_OPTION
from repod.files import Package
from repod.repo import SyncDatabase


def exit_on_error(message: str, argparser: ArgumentParser | None = None) -> None:
    """Print a message to stderr, optionally print argparse help and exit with return code 1

    Parameters
    ----------
    message: str
        A message to print to stderr
    argparser: ArgumentParser | None
        An optional Argumentparser on which to call print_help()
    """

    print(message, file=stderr)
    if argparser:
        argparser.print_help()
    exit(1)


def repod_file_package(args: Namespace, settings: SystemSettings | UserSettings) -> None:
    """Package related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for the Package related actions
    settings: SystemSettings | UserSettings
        A Settings instance that is used for deriving repository directories from

    Raises
    ------
    RuntimeError
        If a debug repository is targetted, but any of the supplied packages is not a debug package (can only be
        successfully checked if PkgInfoV2 is used in the package).
        If an invalid subcommand is provided.
    """

    pretty = ORJSON_OPTION if hasattr(args, "pretty") and args.pretty else 0
    match args.package:
        case "inspect":
            for package_path in args.file:
                model = asyncio.run(
                    Package.from_file(
                        package=package_path,
                        signature=Path(str(package_path) + ".sig") if args.with_signature else None,
                    )
                )

                if args.buildinfo:
                    print(dumps(model.buildinfo.dict(), option=pretty).decode("utf-8"))  # type: ignore[attr-defined]
                elif args.mtree:
                    print(dumps(model.mtree.dict(), option=pretty).decode("utf-8"))  # type: ignore[attr-defined]
                elif args.pkginfo:
                    print(dumps(model.pkginfo.dict(), option=pretty).decode("utf-8"))  # type: ignore[attr-defined]
                else:
                    print(dumps(model.dict(), option=pretty).decode("utf-8"))
        case _:
            exit_on_error(
                message="No subcommand provided to the 'package' command!\n",
                argparser=argparse.ArgParseFactory.repod_file(),
            )


def repod_file_repo_importpkg(args: Namespace, settings: SystemSettings | UserSettings) -> None:
    """Import a package (optionally with signature file) to a repository and write its sync databases

    Parameters
    ----------
    args: Namespace
        The options used for repo related actions
    settings: SystemSettings | UserSettings
        A Settings instance that is used for deriving repository directories from
    """

    if args.dry_run:
        add_packages_dryrun(
            settings=settings,
            files=args.file,
            repo_name=args.name,
            repo_architecture=args.architecture,
            debug_repo=args.debug,
            with_signature=args.with_signature,
            pkgbase_urls=dict(args.source_url),
        )
        return

    add_packages(
        settings=settings,
        files=args.file,
        repo_name=args.name,
        repo_architecture=args.architecture,
        debug_repo=args.debug,
        staging_repo=args.staging,
        testing_repo=args.testing,
        with_signature=args.with_signature,
        pkgbase_urls=dict(args.source_url),
    )


def repod_file_repo(args: Namespace, settings: SystemSettings | UserSettings) -> None:
    """Repository related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for repo related actions
    settings: SystemSettings | UserSettings
        A Settings instance that is used for deriving repository directories from

    Raises
    ------
    RuntimeError
        If an invalid subcommand is provided.
    """

    match args.repo:
        case "importdb":
            management_repo_dir = settings.get_repo_path(
                repo_type=RepoDirTypeEnum.MANAGEMENT,
                name=args.name,
                architecture=args.architecture,
                debug=args.debug,
                staging=args.staging,
                testing=args.testing,
            )
            for base, outputpackagebase in asyncio.run(
                SyncDatabase(
                    database=args.file,
                    desc_version=settings.syncdb_settings.desc_version,
                    files_version=settings.syncdb_settings.files_version,
                ).outputpackagebases()
            ):
                with open(management_repo_dir / f"{base}.json", "wb") as output_file:
                    output_file.write(dumps(outputpackagebase.dict(), option=ORJSON_OPTION))
        case "importpkg":
            repod_file_repo_importpkg(args=args, settings=settings)
        case "writedb":
            write_sync_databases(
                settings=settings,
                repo_name=args.name,
                repo_architecture=args.architecture,
                debug_repo=args.debug,
                staging_repo=args.staging,
                testing_repo=args.testing,
            )
        case _:
            exit_on_error(
                message="No subcommand provided to the 'repo' command!\n",
                argparser=argparse.ArgParseFactory.repod_file(),
            )


def repod_file_schema(args: Namespace) -> None:
    """JSON schema related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for the JSON schema related actions

    Raises
    ------
    RuntimeError
        If an invalid subcommand is provided.
    """

    match args.schema:
        case "export":
            export_schemas(output=args.dir)
        case _:
            exit_on_error(
                message="No subcommand provided to the 'schema' command!\n",
                argparser=argparse.ArgParseFactory.repod_file(),
            )


def repod_file() -> None:
    """The entry point for the repod-file script"""

    try:
        args = argparse.ArgParseFactory.repod_file().parse_args()
    except (argparse.ArgumentTypeError) as e:
        raise RuntimeError(e)

    loglevel = WARNING

    if args.verbose_mode:
        loglevel = INFO
    if args.debug_mode:
        loglevel = DEBUG

    logger = getLogger()
    logger.setLevel(loglevel)
    ch = StreamHandler(stream=stdout)
    ch.setLevel(loglevel)
    logger.addHandler(ch)
    debug(f"ArgumentParser: {args}")

    with patch("repod.config.settings.CUSTOM_CONFIG", args.config):
        settings = SystemSettings() if args.system else UserSettings()
    debug(f"Settings: {settings}")

    match args.subcommand:
        case "package":
            repod_file_package(args=args, settings=settings)  # type: ignore[arg-type]
        case "repo":
            repod_file_repo(args=args, settings=settings)  # type: ignore[arg-type]
        case "schema":
            repod_file_schema(args=args)
        case _:
            exit_on_error(
                message="No subcommand specified!\n",
                argparser=argparse.ArgParseFactory.repod_file(),
            )
