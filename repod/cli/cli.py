import asyncio
from argparse import ArgumentParser, Namespace
from logging import DEBUG, INFO, WARNING, StreamHandler, debug, getLogger
from pathlib import Path
from sys import exit, stderr, stdout
from typing import Optional, Union
from unittest.mock import patch

from orjson import OPT_APPEND_NEWLINE, OPT_INDENT_2, OPT_SORT_KEYS, dumps

from repod import export_schemas
from repod.action.task import (
    AddToRepoTask,
    CreateOutputPackageBasesTask,
    FilesToRepoDirTask,
    MoveTmpFilesTask,
    PrintOutputPackageBasesTask,
    RemoveBackupFilesTask,
    WriteOutputPackageBasesToTmpFileInDirTask,
    WriteSyncDbsToTmpFilesInDirTask,
)
from repod.cli import argparse
from repod.common.enums import ActionStateEnum, RepoDirTypeEnum, RepoFileEnum
from repod.config import SystemSettings, UserSettings
from repod.files import Package
from repod.repo import SyncDatabase

ORJSON_OPTION = OPT_INDENT_2 | OPT_APPEND_NEWLINE | OPT_SORT_KEYS


def exit_on_error(message: str, argparser: Optional[ArgumentParser] = None) -> None:
    """Print a message to stderr, optionally print argparse help and exit with return code 1

    Parameters
    ----------
    message: str
        A message to print to stderr
    argparser: Optional[ArgumentParser]
        An optional Argumentparser on which to call print_help()
    """

    print(message, file=stderr)
    if argparser:
        argparser.print_help()
    exit(1)


def repod_file_package(args: Namespace, settings: Union[SystemSettings, UserSettings]) -> None:
    """Package related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for the Package related actions
    settings: Union[SystemSettings, UserSettings]
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


def repod_file_repo_importpkg(args: Namespace, settings: Union[SystemSettings, UserSettings]) -> None:
    """Import a package (optionally with signature file) to a repository and write its sync databases

    Parameters
    ----------
    args: Namespace
        The options used for repo related actions
    settings: Union[SystemSettings, UserSettings]
        A Settings instance that is used for deriving repository directories from

    Raises
    ------
    RuntimeError
        If an invalid subcommand is provided.
    """

    if args.dry_run:
        print_task = PrintOutputPackageBasesTask(
            dumps_option=ORJSON_OPTION if hasattr(args, "pretty") and args.pretty else 0,
            dependencies=[
                CreateOutputPackageBasesTask(
                    package_paths=args.file,
                    with_signature=args.with_signature,
                    debug_repo=args.debug,
                    package_verification=settings.package_verification,
                )
            ],
        )
        if print_task() != ActionStateEnum.SUCCESS:
            print_task.undo()
            exit_on_error("An error occured while trying to add packages to a repository in a dry-run!")
            return

        return  # pragma: no cover

    add_to_repo_dependencies = [
        MoveTmpFilesTask(
            dependencies=[
                WriteOutputPackageBasesToTmpFileInDirTask(
                    directory=settings.get_repo_path(
                        repo_type=RepoDirTypeEnum.MANAGEMENT,
                        name=args.name,
                        architecture=args.architecture,
                        debug=args.debug,
                        staging=args.staging,
                        testing=args.testing,
                    ),
                    dependencies=[
                        CreateOutputPackageBasesTask(
                            package_paths=args.file,
                            with_signature=args.with_signature,
                            debug_repo=args.debug,
                            package_verification=settings.package_verification,
                        )
                    ],
                )
            ]
        ),
        FilesToRepoDirTask(
            files=args.file,
            file_type=RepoFileEnum.PACKAGE,
            settings=settings,
            name=args.name,
            architecture=args.architecture,
            debug_repo=args.debug,
            staging_repo=args.staging,
            testing_repo=args.testing,
        ),
    ]

    if args.with_signature:
        add_to_repo_dependencies.append(
            FilesToRepoDirTask(
                files=[Path(str(file) + ".sig") for file in args.file],
                file_type=RepoFileEnum.PACKAGE_SIGNATURE,
                settings=settings,
                name=args.name,
                architecture=args.architecture,
                debug_repo=args.debug,
                staging_repo=args.staging,
                testing_repo=args.testing,
            )
        )

    add_to_repo_dependencies.append(
        MoveTmpFilesTask(
            dependencies=[
                WriteSyncDbsToTmpFilesInDirTask(
                    compression=settings.get_repo_database_compression(name=args.name, architecture=args.architecture),
                    desc_version=settings.syncdb_settings.desc_version,
                    files_version=settings.syncdb_settings.files_version,
                    management_repo_dir=settings.get_repo_path(
                        repo_type=RepoDirTypeEnum.MANAGEMENT,
                        name=args.name,
                        architecture=args.architecture,
                        debug=args.debug,
                        staging=args.staging,
                        testing=args.testing,
                    ),
                    package_repo_dir=settings.get_repo_path(
                        repo_type=RepoDirTypeEnum.PACKAGE,
                        name=args.name,
                        architecture=args.architecture,
                        debug=args.debug,
                        staging=args.staging,
                        testing=args.testing,
                    ),
                ),
            ],
        ),
    )

    add_to_repo_task = AddToRepoTask(dependencies=add_to_repo_dependencies)
    if add_to_repo_task() != ActionStateEnum.SUCCESS:
        add_to_repo_task.undo()
        exit_on_error("An error occured while trying to add packages to a repository!")
        return

    remove_backup_files_task = RemoveBackupFilesTask(
        dependencies=[task for task in add_to_repo_task.dependencies if isinstance(task, MoveTmpFilesTask)]
    )
    remove_backup_files_task()

    return


def repod_file_repo(args: Namespace, settings: Union[SystemSettings, UserSettings]) -> None:
    """Repository related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for repo related actions
    settings: Union[SystemSettings, UserSettings]
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
            remove_backup_files_task = RemoveBackupFilesTask(
                dependencies=[
                    MoveTmpFilesTask(
                        dependencies=[
                            WriteSyncDbsToTmpFilesInDirTask(
                                compression=settings.get_repo_database_compression(
                                    name=args.name, architecture=args.architecture
                                ),
                                desc_version=settings.syncdb_settings.desc_version,
                                files_version=settings.syncdb_settings.files_version,
                                management_repo_dir=settings.get_repo_path(
                                    repo_type=RepoDirTypeEnum.MANAGEMENT,
                                    name=args.name,
                                    architecture=args.architecture,
                                    debug=args.debug,
                                    staging=args.staging,
                                    testing=args.testing,
                                ),
                                package_repo_dir=settings.get_repo_path(
                                    repo_type=RepoDirTypeEnum.PACKAGE,
                                    name=args.name,
                                    architecture=args.architecture,
                                    debug=args.debug,
                                    staging=args.staging,
                                    testing=args.testing,
                                ),
                            ),
                        ],
                    )
                ]
            )
            remove_backup_files_task()
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
