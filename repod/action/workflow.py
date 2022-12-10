"""Workflows describing common repository actions."""
from logging import debug
from pathlib import Path
from sys import exit, stderr

from pydantic import AnyUrl

from repod.action.task import (
    AddToArchiveTask,
    AddToRepoTask,
    CleanupRepoTask,
    ConsolidateOutputPackageBasesTask,
    CreateOutputPackageBasesTask,
    FilesToRepoDirTask,
    MoveTmpFilesTask,
    PrintOutputPackageBasesTask,
    RemoveBackupFilesTask,
    RemoveManagementRepoSymlinksTask,
    RemovePackageRepoSymlinksTask,
    RepoGroupTask,
    ReproducibleBuildEnvironmentTask,
    Task,
    WriteOutputPackageBasesToTmpFileInDirTask,
    WriteSyncDbsToTmpFilesInDirTask,
)
from repod.common.enums import (
    ActionStateEnum,
    ArchitectureEnum,
    RepoDirTypeEnum,
    RepoFileEnum,
    RepoTypeEnum,
)
from repod.config.settings import ArchiveSettings, SystemSettings, UserSettings


def exit_on_error(message: str) -> None:
    """Print a message to stderr, optionally print argparse help and exit with return code 1.

    Parameters
    ----------
    message: str
        A message to print to stderr
    """
    print(message, file=stderr)
    stderr.write(message)
    exit(1)


def add_packages_dryrun(
    settings: SystemSettings | UserSettings,
    files: list[Path],
    repo_name: Path,
    repo_architecture: ArchitectureEnum,
    debug_repo: bool,
    with_signature: bool,
    pkgbase_urls: dict[str, AnyUrl] | None,
) -> None:
    """Print output of package representation in the management repository if packages were added.

    Parameters
    ----------
    settings: SystemSettings | UserSettings
        Settings object to retrieve data about the repository from
    files: list[Path]
        The package files to add
    repo_name: Path
        The name of the repository to add packages to
    repo_architecture: ArchitectureEnum | None
        The optional architecture of the repository to add packages to
    debug_repo: bool
        A boolean value indicating whether the packages target a debug repository
    with_signature: bool
        A boolean value indicating whether the signatures of the packages are also added
    pkgbase_urls: dict[str, AnyUrl] | None
        An optional dict, providing pkgbases and their source URLs
    """
    debug(f"Adding packages in a dry-run: {files}")
    print_task = PrintOutputPackageBasesTask(
        dumps_option=settings.get_repo_management_repo(
            name=repo_name, architecture=repo_architecture
        ).json_dumps_option,
        dependencies=[
            CreateOutputPackageBasesTask(
                architecture=settings.get_repo_architecture(name=repo_name, architecture=repo_architecture),
                package_paths=files,
                with_signature=with_signature,
                debug_repo=debug_repo,
                package_verification=settings.package_verification,
                pkgbase_urls=pkgbase_urls,
            )
        ],
    )
    if print_task() != ActionStateEnum.SUCCESS:
        print_task.undo()
        exit_on_error("An error occured while trying to add packages to a repository in a dry-run!")
        return

    return


def add_packages(
    settings: SystemSettings | UserSettings,
    files: list[Path],
    repo_name: Path,
    repo_architecture: ArchitectureEnum | None,
    debug_repo: bool,
    staging_repo: bool,
    testing_repo: bool,
    with_signature: bool,
    pkgbase_urls: dict[str, AnyUrl] | None,
) -> None:
    """Add packages to a repository.

    Parameters
    ----------
    settings: SystemSettings | UserSettings
        Settings object to retrieve data about the repository from
    files: list[Path]
        The package files to add
    repo_name: Path
        The name of the repository to add packages to
    repo_architecture: ArchitectureEnum | None
        The optional architecture of the repository to add packages to
    debug_repo: bool
        A boolean value indicating whether the packages target a debug repository
    staging_repo: bool
        A boolean value indicating whether the packages target a staging repository
    testing_repo: bool
        A boolean value indicating whether the packages target a testing repository
    with_signature: bool
        A boolean value indicating whether the signatures of the packages are also added
    pkgbase_urls: dict[str, AnyUrl] | None
        An optional dict, providing pkgbases and their source URLs
    """
    debug(f"Adding packages: {files}")
    debug(f"Provided urls: {pkgbase_urls}")

    repo = settings.get_repo(name=repo_name, architecture=repo_architecture)

    add_to_repo_dependencies: list[Task] = []

    management_repo_dir = settings.get_repo_path(
        repo_dir_type=RepoDirTypeEnum.MANAGEMENT,
        name=repo_name,
        architecture=repo_architecture,
        repo_type=RepoTypeEnum.from_bool(
            debug=debug_repo,
            staging=staging_repo,
            testing=testing_repo,
        ),
    )
    package_repo_dir = settings.get_repo_path(
        repo_dir_type=RepoDirTypeEnum.PACKAGE,
        name=repo_name,
        architecture=repo_architecture,
        repo_type=RepoTypeEnum.from_bool(
            debug=debug_repo,
            staging=staging_repo,
            testing=testing_repo,
        ),
    )

    outputpackagebasestask = CreateOutputPackageBasesTask(
        architecture=settings.get_repo_architecture(name=repo_name, architecture=repo_architecture),
        package_paths=files,
        with_signature=with_signature,
        debug_repo=debug_repo,
        pkgbase_urls=pkgbase_urls,
        package_verification=settings.package_verification,
    )
    consolidateoutputpackagebases = ConsolidateOutputPackageBasesTask(
        directory=management_repo_dir,
        stability_layer_dirs=settings.get_management_repo_stability_paths(
            name=repo_name,
            architecture=repo_architecture,
            repo_type=RepoTypeEnum.from_bool(
                debug=debug_repo,
                staging=staging_repo,
                testing=testing_repo,
            ),
        ),
        url_validation_settings=repo.package_url_validation,
        dependencies=[
            outputpackagebasestask,
        ],
    )

    package_files_task = FilesToRepoDirTask(
        files=files,
        file_type=RepoFileEnum.PACKAGE,
        settings=settings,
        name=repo_name,
        architecture=repo_architecture,
        repo_type=RepoTypeEnum.from_bool(
            debug=debug_repo,
            staging=staging_repo,
            testing=testing_repo,
        ),
    )

    if repo.build_requirements_exist:
        reproduciblebuildenvironmenttask = ReproducibleBuildEnvironmentTask(
            management_directories=[management_repo_dir],
            archive_dir=repo.archiving.packages if repo.archiving else None,  # type: ignore[union-attr]
            dependencies=[
                outputpackagebasestask,
            ],
        )
        add_to_repo_dependencies.append(reproduciblebuildenvironmenttask)

    if repo.group:
        add_to_repo_dependencies.append(
            RepoGroupTask(
                repositories=settings.get_repos_by_group(group=repo.group, exclude_repo=repo),
                dependencies=[
                    outputpackagebasestask,
                ],
            )
        )

    add_to_repo_dependencies.append(
        MoveTmpFilesTask(
            dependencies=[
                consolidateoutputpackagebases,
                WriteOutputPackageBasesToTmpFileInDirTask(
                    directory=management_repo_dir,
                    dumps_option=settings.get_repo_management_repo(
                        name=repo_name, architecture=repo_architecture
                    ).json_dumps_option,
                    dependencies=[
                        outputpackagebasestask,
                    ],
                ),
            ]
        ),
    )
    add_to_repo_dependencies.append(package_files_task)

    add_to_archive_dependencies = [
        package_files_task,
    ]

    if with_signature:
        signature_files_task = FilesToRepoDirTask(
            files=[Path(str(file) + ".sig") for file in files],
            file_type=RepoFileEnum.PACKAGE_SIGNATURE,
            settings=settings,
            name=repo_name,
            architecture=repo_architecture,
            repo_type=RepoTypeEnum.from_bool(
                debug=debug_repo,
                staging=staging_repo,
                testing=testing_repo,
            ),
        )
        add_to_repo_dependencies.append(signature_files_task)
        add_to_archive_dependencies.append(signature_files_task)

    add_to_repo_dependencies.append(
        MoveTmpFilesTask(
            dependencies=[
                WriteSyncDbsToTmpFilesInDirTask(
                    compression=settings.get_repo_database_compression(name=repo_name, architecture=repo_architecture),
                    desc_version=settings.syncdb_settings.desc_version,
                    files_version=settings.syncdb_settings.files_version,
                    management_repo_dir=management_repo_dir,
                    package_repo_dir=package_repo_dir,
                ),
            ],
        ),
    )
    if isinstance(repo.archiving, ArchiveSettings):
        add_to_repo_dependencies.append(
            AddToArchiveTask(
                archive_dir=repo.archiving.packages,
                dependencies=add_to_archive_dependencies,  # type: ignore[arg-type]
            )
        )

    add_to_repo_task = AddToRepoTask(dependencies=add_to_repo_dependencies)
    if add_to_repo_task() != ActionStateEnum.SUCCESS:
        add_to_repo_task.undo()
        exit_on_error("An error occured while trying to add packages to a repository!")
        return

    cleanup_repo_task = CleanupRepoTask(
        dependencies=[
            RemovePackageRepoSymlinksTask(
                directory=package_repo_dir,
                dependencies=[consolidateoutputpackagebases],
            ),
            RemoveManagementRepoSymlinksTask(
                directory=management_repo_dir,
                dependencies=[consolidateoutputpackagebases],
            ),
            RemoveBackupFilesTask(
                dependencies=[task for task in add_to_repo_task.dependencies if isinstance(task, MoveTmpFilesTask)]
            ),
        ],
    )
    cleanup_repo_task()

    return


def write_sync_databases(
    settings: SystemSettings | UserSettings,
    repo_name: Path,
    repo_architecture: ArchitectureEnum | None,
    debug_repo: bool,
    staging_repo: bool,
    testing_repo: bool,
) -> None:
    """Write the sync databases of a repository.

    Parameters
    ----------
    settings: SystemSettings | UserSettings
        Settings object to retrieve data about the repository from
    repo_name: Path
        The name of the repository
    repo_architecture: ArchitectureEnum | None
        The optional architecture of the repository
    debug_repo: bool
        A boolean value indicating whether to target a debug repository
    staging_repo: bool
        A boolean value indicating whether to target a staging repository
    testing_repo: bool
        A boolean value indicating whether to target a testing repository
    """
    movetmpfilestask = MoveTmpFilesTask(
        dependencies=[
            WriteSyncDbsToTmpFilesInDirTask(
                compression=settings.get_repo_database_compression(name=repo_name, architecture=repo_architecture),
                desc_version=settings.syncdb_settings.desc_version,
                files_version=settings.syncdb_settings.files_version,
                management_repo_dir=settings.get_repo_path(
                    repo_dir_type=RepoDirTypeEnum.MANAGEMENT,
                    name=repo_name,
                    architecture=repo_architecture,
                    repo_type=RepoTypeEnum.from_bool(
                        debug=debug_repo,
                        staging=staging_repo,
                        testing=testing_repo,
                    ),
                ),
                package_repo_dir=settings.get_repo_path(
                    repo_dir_type=RepoDirTypeEnum.PACKAGE,
                    name=repo_name,
                    architecture=repo_architecture,
                    repo_type=RepoTypeEnum.from_bool(
                        debug=debug_repo,
                        staging=staging_repo,
                        testing=testing_repo,
                    ),
                ),
            ),
        ],
    )
    if movetmpfilestask() != ActionStateEnum.SUCCESS:
        movetmpfilestask.undo()
        exit_on_error("An error occured while trying to write a repository's sync databases!")
        return

    remove_backup_files_task = RemoveBackupFilesTask(dependencies=[movetmpfilestask])
    remove_backup_files_task()

    return
