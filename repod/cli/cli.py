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
    PkgTypeEnum,
    PkgVerificationTypeEnum,
    RepoFileEnum,
    RepoTypeEnum,
)
from repod.config import SystemSettings, UserSettings
from repod.files import Package
from repod.files.pkginfo import PkgInfoV2
from repod.repo import OutputPackageBase, SyncDatabase
from repod.repo.package import RepoDbTypeEnum, RepoFile
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
        case _:
            raise RuntimeError(f"Invalid subcommand {args.package} provided to the 'package' command!")


def repod_file_repo_importpkg(args: Namespace, settings: Union[SystemSettings, UserSettings]) -> None:
    """Import a package (optionally with signature file) to a repository

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

    pretty = ORJSON_OPTION if hasattr(args, "pretty") and args.pretty else 0

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
                raise RuntimeError(f"Verification of package {package_path} with signature {signature_path} failed!")

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
                f"The debug repository of {args.name} is targetted, "
                "but not all provided packages are debug packages!"
            )
    else:
        if any(
            [
                True
                for package in packages
                if isinstance(
                    package.pkginfo,  # type: ignore[attr-defined]
                    PkgInfoV2,
                )
                and package.pkginfo.pkgtype == PkgTypeEnum.DEBUG.value  # type: ignore[attr-defined]
            ]
        ):
            raise RuntimeError(
                f"A non-debug repository of {args.name} is targetted, "
                "but not all provided packages are non-debug packages!"
            )

    outputpackagebase = OutputPackageBase.from_package(packages=packages)

    if args.dry_run:
        print(dumps(outputpackagebase.dict(), option=pretty).decode("utf-8"))
        return

    pkgbase = outputpackagebase.base  # type: ignore[attr-defined]
    management_repo_dir = settings.get_repo_path(
        repo_type=RepoTypeEnum.MANAGEMENT,
        name=args.name,
        architecture=args.architecture,
        debug=args.debug,
        staging=args.staging,
        testing=args.testing,
    )
    with open(management_repo_dir / f"{pkgbase}.json", "wb") as output_file:
        output_file.write(dumps(outputpackagebase.dict(), option=ORJSON_OPTION))

    package_repo_dir = settings.get_repo_path(
        repo_type=RepoTypeEnum.PACKAGE,
        name=args.name,
        architecture=args.architecture,
        debug=args.debug,
        staging=args.staging,
        testing=args.testing,
    )
    package_pool_dir = settings.get_repo_path(
        repo_type=RepoTypeEnum.POOL,
        name=args.name,
        architecture=args.architecture,
        debug=args.debug,
        staging=args.staging,
        testing=args.testing,
    )
    for package_path in args.file:
        package_file = RepoFile(
            file_type=RepoFileEnum.PACKAGE,
            file_path=package_pool_dir / package_path.name,
            symlink_path=package_repo_dir / package_path.name,
        )
        package_file.copy_from(path=package_path)
        package_file.link()
        if args.with_signature:
            signature_path = Path(str(package_path) + ".sig")
            signature_file = RepoFile(
                file_type=RepoFileEnum.PACKAGE_SIGNATURE,
                file_path=package_pool_dir / signature_path.name,
                symlink_path=package_repo_dir / signature_path.name,
            )
            signature_file.copy_from(path=signature_path)
            signature_file.link()


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
                repo_type=RepoTypeEnum.MANAGEMENT,
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
            compression = settings.get_repo_database_compression(name=args.name, architecture=args.architecture)
            package_repo_dir = settings.get_repo_path(
                repo_type=RepoTypeEnum.PACKAGE,
                name=args.name,
                architecture=args.architecture,
                debug=args.debug,
                staging=args.staging,
                testing=args.testing,
            )
            default_syncdb_path = package_repo_dir / Path(package_repo_dir.parent.name + ".db.tar." + compression.value)
            default_syncdb_symlink_path = package_repo_dir / Path(package_repo_dir.parent.name + ".db")
            files_syncdb_path = package_repo_dir / Path(
                package_repo_dir.parent.name + ".files.tar." + compression.value
            )
            files_syncdb_symlink_path = package_repo_dir / Path(package_repo_dir.parent.name + ".files")

            default_sync_db = SyncDatabase(
                database=default_syncdb_path,
                database_type=RepoDbTypeEnum.DEFAULT,
                compression_type=compression,
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
            )
            management_repo_dir = settings.get_repo_path(
                repo_type=RepoTypeEnum.MANAGEMENT,
                name=args.name,
                architecture=args.architecture,
                debug=args.debug,
                staging=args.staging,
                testing=args.testing,
            )
            asyncio.run(default_sync_db.stream_management_repo(path=management_repo_dir))
            default_syncdb_symlink_path.unlink(missing_ok=True)
            default_syncdb_symlink_path.symlink_to(default_syncdb_path.relative_to(default_syncdb_symlink_path.parent))

            files_sync_db = SyncDatabase(
                database=files_syncdb_path,
                database_type=RepoDbTypeEnum.FILES,
                compression_type=compression,
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
            )
            asyncio.run(files_sync_db.stream_management_repo(path=management_repo_dir))
            files_syncdb_symlink_path.unlink(missing_ok=True)
            files_syncdb_symlink_path.symlink_to(files_syncdb_path.relative_to(files_syncdb_symlink_path.parent))
        case _:
            raise RuntimeError(f"Invalid subcommand {args.repo} provided to the 'repo' command!")


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
            raise RuntimeError("Invalid subcommand provided!")
