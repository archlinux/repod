import asyncio
from argparse import Namespace
from logging import DEBUG, INFO, WARNING, StreamHandler, debug, getLogger
from pathlib import Path
from sys import stdout
from typing import List, Union
from unittest.mock import patch

from orjson import OPT_APPEND_NEWLINE, OPT_INDENT_2, OPT_SORT_KEYS, dumps

from repod import export_schemas
from repod.cli import argparse
from repod.common.enums import (
    CompressionTypeEnum,
    PkgTypeEnum,
    PkgVerificationTypeEnum,
    RepoTypeEnum,
)
from repod.config import SystemSettings, UserSettings
from repod.files import Package
from repod.files.pkginfo import PkgInfoV2
from repod.repo import OutputPackageBase, SyncDatabase
from repod.repo.package import RepoDbTypeEnum
from repod.verification import PacmanKeyVerifier

ORJSON_OPTION = OPT_INDENT_2 | OPT_APPEND_NEWLINE | OPT_SORT_KEYS


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

        case "import":
            packages: List[Package] = []
            for package_path in args.file:
                signature_path = Path(str(package_path) + ".sig") if args.with_signature else None
                if settings.package_verification == PkgVerificationTypeEnum.PACMANKEY and args.with_signature:
                    debug(f"Verifying package signature based on {settings.package_verification.value}...")
                    verifier = PacmanKeyVerifier()
                    if verifier.verify(
                        package=package_path,
                        signature=signature_path,  # type: ignore[arg-type]
                    ):
                        debug("Package signature successfully verified!")
                    else:
                        raise RuntimeError(
                            f"Verification of package {package_path} with signature {signature_path} failed!"
                        )

                packages.append(
                    asyncio.run(
                        Package.from_file(
                            package=package_path,
                            signature=signature_path,
                        )
                    )
                )

            if args.debug:
                if any(
                    [
                        True
                        for package in packages
                        if isinstance(
                            package.pkginfo,  # type: ignore[attr-defined]
                            PkgInfoV2,
                        )
                        and package.pkginfo.pkgtype != PkgTypeEnum.DEBUG.value  # type: ignore[attr-defined]
                    ]
                ):
                    raise RuntimeError(
                        f"The debug repository of {args.repo} is targetted, "
                        "but not all provided packages are debug packages!"
                    )

            outputpackagebase = OutputPackageBase.from_package(packages=packages)
            if args.dry_run:
                print(dumps(outputpackagebase.dict(), option=pretty).decode("utf-8"))
            else:
                pkgbase = outputpackagebase.base  # type: ignore[attr-defined]
                management_repo_dir = settings.get_repo_path(
                    repo_type=RepoTypeEnum.MANAGEMENT,
                    name=args.repo,
                    debug=args.debug,
                    staging=args.staging,
                    testing=args.testing,
                )
                with open(management_repo_dir / f"{pkgbase}.json", "wb") as output_file:
                    output_file.write(dumps(outputpackagebase.dict(), option=ORJSON_OPTION))
        case _:
            raise RuntimeError(f"Invalid subcommand {args.package} provided to the 'package' command!")


def repod_file_management(args: Namespace, settings: Union[SystemSettings, UserSettings]) -> None:
    """Management repo related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for the management repo related actions
    settings: Union[SystemSettings, UserSettings]
        A Settings instance that is used for deriving repository directories from

    Raises
    ------
    RuntimeError
        If an invalid subcommand is provided.
    """

    match args.management:
        case "import":
            management_repo_dir = settings.get_repo_path(
                repo_type=RepoTypeEnum.MANAGEMENT,
                name=args.repo,
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
        case "export":
            if "".join(args.file.suffixes) not in CompressionTypeEnum.as_db_file_suffixes():
                raise RuntimeError(
                    "The file path needs to point at a default repository sync database that has one of the supported "
                    f"suffixes: {CompressionTypeEnum.as_db_file_suffixes()}"
                )

            compression = CompressionTypeEnum.from_string(input_=args.compression)
            default_sync_db = SyncDatabase(
                database=args.file,
                database_type=RepoDbTypeEnum.DEFAULT,
                compression_type=compression,
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
            )
            management_repo_dir = settings.get_repo_path(
                repo_type=RepoTypeEnum.MANAGEMENT,
                name=args.repo,
                debug=args.debug,
                staging=args.staging,
                testing=args.testing,
            )
            asyncio.run(default_sync_db.stream_management_repo(path=management_repo_dir))

            files_sync_db = SyncDatabase(
                database=Path("/".join(part.replace(".db", ".files") for part in args.file.parts)),
                database_type=RepoDbTypeEnum.FILES,
                compression_type=compression,
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
            )
            asyncio.run(files_sync_db.stream_management_repo(path=management_repo_dir))
        case _:
            raise RuntimeError(f"Invalid subcommand {args.management} provided to the 'management' command!")


def repod_file_syncdb(args: Namespace, settings: Union[SystemSettings, UserSettings]) -> None:
    """Repository sync database related actions from the repod-file script

    Parameters
    ----------
    args: Namespace
        The options used for the repository sync database related actions
    settings: Union[SystemSettings, UserSettings]
        A Settings instance that is used for deriving repository directories from

    Raises
    ------
    RuntimeError
        If an invalid subcommand is provided.
    """

    match args.syncdb:
        case "import":
            if "".join(args.file.suffixes) not in CompressionTypeEnum.as_db_file_suffixes():
                raise RuntimeError(
                    "The file path needs to point at a default repository sync database that has one of the supported "
                    f"suffixes: {CompressionTypeEnum.as_db_file_suffixes()}"
                )

            compression = CompressionTypeEnum.from_string(input_=args.compression)
            default_sync_db = SyncDatabase(
                database=args.file,
                database_type=RepoDbTypeEnum.DEFAULT,
                compression_type=compression,
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
            )
            management_repo_dir = settings.get_repo_path(
                repo_type=RepoTypeEnum.MANAGEMENT,
                name=args.repo,
                debug=args.debug,
                staging=args.staging,
                testing=args.testing,
            )
            asyncio.run(default_sync_db.stream_management_repo(path=management_repo_dir))
            files_sync_db = SyncDatabase(
                database=Path("/".join(part.replace(".db", ".files") for part in args.file.parts)),
                database_type=RepoDbTypeEnum.FILES,
                compression_type=compression,
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
            )
            asyncio.run(files_sync_db.stream_management_repo(path=management_repo_dir))
        case "export":
            management_repo_dir = settings.get_repo_path(
                repo_type=RepoTypeEnum.MANAGEMENT,
                name=args.repo,
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
        case _:
            raise RuntimeError(f"Invalid subcommand {args.syncdb} provided to the 'syncdb' command!")


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
            raise RuntimeError(f"Invalid subcommand {args.schema} provided to the 'schema' command!")


def repod_file() -> None:
    """The entry point for the repod-file script"""

    try:
        args = argparse.ArgParseFactory.repod_file().parse_args()
    except (argparse.ArgumentTypeError) as e:
        raise RuntimeError(e)

    loglevel = WARNING

    if args.verbose:
        loglevel = INFO
    if args.debug:
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
        case "management":
            repod_file_management(args=args, settings=settings)  # type: ignore[arg-type]
        case "syncdb":
            repod_file_syncdb(args=args, settings=settings)  # type: ignore[arg-type]
        case "schema":
            repod_file_schema(args=args)
        case _:
            raise RuntimeError("Invalid subcommand provided!")
