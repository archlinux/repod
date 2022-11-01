from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from itertools import groupby
from logging import debug, info
from operator import attrgetter
from pathlib import Path
from re import sub
from shutil import copy2

from orjson import JSONEncodeError, dumps
from pydantic import AnyUrl, BaseModel, ValidationError, validator

from repod.action.check import (
    Check,
    DebugPackagesCheck,
    MatchingArchitectureCheck,
    PackagesNewOrUpdatedCheck,
    PacmanKeyPackagesSignatureVerificationCheck,
    PkgbasesVersionUpdateCheck,
    SourceUrlCheck,
)
from repod.common.enums import (
    ActionStateEnum,
    ArchitectureEnum,
    CompressionTypeEnum,
    FilesVersionEnum,
    PackageDescVersionEnum,
    PkgVerificationTypeEnum,
    RepoDirTypeEnum,
    RepoFileEnum,
)
from repod.config import SystemSettings, UserSettings
from repod.config.defaults import ORJSON_OPTION
from repod.config.settings import UrlValidationSettings
from repod.errors import RepoManagementFileError, RepoManagementFileNotFoundError
from repod.files import Package
from repod.repo import OutputPackageBase, SyncDatabase
from repod.repo.package import RepoDbTypeEnum, RepoFile
from repod.repo.package.repofile import relative_to_shared_base


class SourceDestination(BaseModel):
    """A model describing a source and a destination of a file

    Attributes
    ----------
    source: Path
        The source file (Path must have '.tmp' suffix)
    destination: Path
        The destination file
    destination_backup: Path
        The Path of the backup of destination (Path must have '.bkp' suffix)
    backup_done: bool
        Whether the destination exists and whether a backup of it has been created (defaults to False)
    """

    source: Path
    destination: Path
    destination_backup: Path
    backup_done: bool = False

    @validator("source")
    def validate_source(cls, path: Path) -> Path:
        """Validate the source attribute

        Raises
        ------
        ValueError
            If source does not have a .tmp suffix,
            or if source is not an absolute Path

        Parameters
        ----------
        path: Path
            A Path to validate

        Returns
        -------
        Path
            A validated Path
        """

        if not path.is_absolute():
            raise ValueError(f"The path Path must be absolute, but {path} is not!")
        if not str(path).endswith(".tmp"):
            raise ValueError(f"The path Path must end with '.tmp', but {path} does not!")

        return path

    @validator("destination")
    def validate_destination(cls, path: Path) -> Path:
        """Validate the destination attribute

        Raises
        ------
        ValueError
            If destination has a .tmp or .bkp suffix,
            or if destination is not an absolute Path

        Parameters
        ----------
        path: Path
            A Path to validate

        Returns
        -------
        Path
            A validated Path
        """

        if not path.is_absolute():
            raise ValueError(f"The destination Path must be absolute, but {path} is not!")
        if str(path).endswith(".tmp"):
            raise ValueError(f"The destination Path must not end with '.tmp', but {path} does!")
        if str(path).endswith(".bkp"):
            raise ValueError(f"The destination Path must not end with '.bkp', but {path} does!")

        return path

    @validator("destination_backup")
    def validate_destination_backup(cls, path: Path) -> Path:
        """Validate the destination_backup attribute

        Raises
        ------
        ValueError
            If destination does not have .bkp suffix,
            or if destination_backup is not an absolute Path

        Parameters
        ----------
        path: Path
            A Path to validate

        Returns
        -------
        Path
            A validated Path
        """
        if not path.is_absolute():
            raise ValueError(f"The destination_backup Path must be absolute, but {path} is not!")
        if not str(path).endswith(".bkp"):
            raise ValueError(f"The destination_backup Path must end with '.bkp', but {path} does not!")

        return path


class Task(ABC):
    """An abstract base class to describe an operation

    Tasks are Callables, that are used to run an operation (e.g. on an input) and may have pre and post checks. A Task
    tracks its own state, which indicates whether it ran successfully or not, using a member of ActionStateEnum.

    When deriving from Task, the do() and undo() methods must be implemented.

    The do() method is automatically run in __call__() and is expected to return either ActionStateEnum.SUCCESS_TASK or
    ActionStateEnum.FAILED_TASK, depending on whether the Task finished successfully or failed (respectively).

    The undo() method must undo all actions that have been done in do(). The method is expected to reset a Task's state
    property back to ActionStateEnum.NOT_STARTED or ActionStateEnum.FAILED_UNDO_TASK and return its state property,
    depending on whether the undo operation finished successfully or failed (respectively).

    Attributes
    ----------
    dependencies: list[Task] | None
        An optional list of Task instances that are run before this task and its pre_checks (defaults to None)
    pre_checks: list[Check]
        A list of Check instances that are called before the Task is called
    post_checks: list[Check]
        A list of Check instances that are called after the Task is run
    state: ActionStateEnum
        A member of ActionStateEnum indicating whether the Task is unstarted, started, failed, failed in any of the pre
        or post checks or successfully finished (defaults to ActionStateEnum.NOT_STARTED)
    """

    dependencies: list[Task] = []
    pre_checks: list[Check] = []
    post_checks: list[Check] = []
    state: ActionStateEnum = ActionStateEnum.NOT_STARTED

    def __call__(self) -> ActionStateEnum:  # pragma: no cover
        """The call for a Task

        A Task has the following call order:
        - all of its dependency Tasks
        - the Checks listed in pre_checks
        - its own do() method
        - the Checks listed in post_checks

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.FAILED_DEPENDENCY if any of the dependency Tasks fails,
            ActionStateEnum.SUCCESS if the Task executed successfully (or is run again after running successfully)
            ActionStateEnum.FAILED_PRE_CHECK if any of the Checks in pre_checks fails,
            ActionStateEnum.FAILED_TASK if the do() method of the Task fails,
            ActionStateEnum.FAILED_POST_CHECK if  any of the Checks in post_checks fails,
        """

        for dependency in self.dependencies:
            if dependency() != ActionStateEnum.SUCCESS:
                self.state = ActionStateEnum.FAILED_DEPENDENCY
                return

        if self.state == ActionStateEnum.SUCCESS:
            return self.state

        self.state = ActionStateEnum.STARTED

        for check in self.pre_checks:
            if check() != ActionStateEnum.SUCCESS:
                self.state = ActionStateEnum.FAILED_PRE_CHECK
                return self.state

        if self.do() != ActionStateEnum.SUCCESS_TASK:
            return self.state

        for check in self.post_checks:
            if check() != ActionStateEnum.SUCCESS:
                self.state = ActionStateEnum.FAILED_POST_CHECK
                return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state

    @abstractmethod
    def do(self) -> ActionStateEnum:  # pragma: no cover
        """Run the Task's operation

        This runs the Task's operation and sets its state property to ActionStateEnum.SUCCESS_TASK or
        ActionStateEnum.FAILED_TASK, depending on whether it runs successful or not.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise.
        """

        pass

    @abstractmethod
    def undo(self) -> ActionStateEnum:  # pragma: no cover
        """Undo the Task's operation

        This runs an operation to undo any actions done in a Task's do() call, sets the Task's state property to
        ActionStateEnum.NOT_STARTED if successful, otherwise to ActionStateEnum.FAILED_UNDO_TASK and returns the state.

        Before returning, implementations of this method are expected to call self.dependency_undo() to also undo any
        dependency tasks in reverse order.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        pass

    def dependency_undo(self) -> ActionStateEnum:  # pragma: no cover
        """Undo all dependency Tasks in reverse order

        Returns
        -------
        ActionStateEnum
            The ActionStateEnum member before calling the method,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed
        """

        for dependency in reversed(self.dependencies):
            if dependency.undo() != ActionStateEnum.NOT_STARTED:
                self.state = ActionStateEnum.FAILED_UNDO_DEPENDENCY

        return self.state

    def is_done(self) -> bool:  # pragma: no cover
        """Return the done state of the Task as a boolean value

        Returns
        -------
        bool
            True if the Task is done (self.state is ActionStateEnum.SUCCESS), False otherwise
        """

        return True if self.state == ActionStateEnum.SUCCESS else False


class CreateOutputPackageBasesTask(Task):
    """A Task to create a list of OutputPackageBase instances from a list of Paths

    If a pkgbase_urls dict is provided, the AnyUrl instances in it, which match the created pkgbases, will be added to
    the respective OutputPackageBase objects.

    Attributes
    ----------
    architecture: ArchitectureEnum
        A member of ArchitectureEnum that specifies the target CPU architecture that the OutputPackageBase instances
        must match
    pkgbases: list[OutputPackageBase]
        A list of OutputPackageBase instances created from the input of the task (defaults to [])
    pkgbase_urls: dict[str, AnyUrl] | None
        An optional dict, providing pkgbases and their source URLs (defaults to None)
    debug_repo: bool
        A boolean value indicating whether a debug repository is targetted
    """

    def __init__(
        self,
        architecture: ArchitectureEnum,
        package_paths: list[Path],
        with_signature: bool,
        debug_repo: bool,
        pkgbase_urls: dict[str, AnyUrl] | None = None,
        package_verification: PkgVerificationTypeEnum | None = None,
        dependencies: list[Task] | None = None,
    ):
        """Initialize an instance of CreateOutputPackageBasesTask

        Parameters
        ----------
        architecture: ArchitectureEnum
            A member of ArchitectureEnum that specifies the target CPU architecture that the OutputPackageBase instances
            must match
        package_paths: list[Path]
            The path to a package file
        with_signature: bool
            A boolean value indicating whether to also consider signature files
        debug_repo: bool
            A boolean value indicating whether a debug repository is targetted
        pkgbase_urls: dict[str, AnyUrl] | None
            An optional dict, providing pkgbases and their source URLs (defaults to None)
        package_verification: PkgVerificationTypeEnum | None
            The type of package verification to be run against the package (defaults to None)
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        pre_checks: list[Check] = []
        post_checks: list[Check] = []

        debug(f"Initializing Task to create instances of OutputPackageBase using paths {package_paths}...")

        self.architecture = architecture
        self.debug_repo = debug_repo

        if dependencies is not None:
            self.dependencies = dependencies

        if with_signature:
            self.package_paths = [[package_path, Path(str(package_path) + ".sig")] for package_path in package_paths]
        else:
            self.package_paths = [[package_path] for package_path in package_paths]

        if with_signature:
            if package_verification == PkgVerificationTypeEnum.PACMANKEY:
                debug(f"Adding pacman-key based verification of packages {self.package_paths} to Task...")
                pre_checks.append(PacmanKeyPackagesSignatureVerificationCheck(packages=self.package_paths))

        self.pkgbase_urls = pkgbase_urls or {}
        self.pre_checks = pre_checks
        self.post_checks = post_checks
        self.pkgbases: list[OutputPackageBase] = []

    def do(self) -> ActionStateEnum:
        """Create instances of OutputPackageBase

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise.
        """

        packages: list[Package] = []

        debug(f"Running Task to create a list of OutputPackageBase instances using {self.package_paths}...")
        self.state = ActionStateEnum.STARTED_TASK

        for package_list in self.package_paths:
            try:
                packages.append(
                    asyncio.run(
                        Package.from_file(
                            package=package_list[0],
                            signature=package_list[1] if len(package_list) == 2 else None,
                        )
                    )
                )
            except RepoManagementFileError as e:
                info(e)
                self.state = ActionStateEnum.FAILED_TASK
                return self.state

        for key, group in groupby(packages, attrgetter("pkginfo.base")):
            debug(f"Create OutputPackageBase representing pkgbase {key}")
            try:
                outputpackagebase = OutputPackageBase.from_package(packages=list(group))
                outputpackagebase.source_url = self.pkgbase_urls.get(  # type: ignore[attr-defined]
                    outputpackagebase.base,  # type: ignore[attr-defined]
                )
                self.pkgbases.append(outputpackagebase)
            except (ValueError, RuntimeError) as e:
                info(e)
                self.state = ActionStateEnum.FAILED_TASK
                return self.state

        self.post_checks.append(DebugPackagesCheck(packages=packages, debug=self.debug_repo))
        self.post_checks.append(MatchingArchitectureCheck(architecture=self.architecture, packages=packages))

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the creation of OutputPackageBase instances

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        debug(f"Undoing Task to create OutputPackageBase instances from packages {self.package_paths}... ")

        self.pkgbases.clear()
        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class PrintOutputPackageBasesTask(Task):
    """A Task to print instances of OutputPackageBase to stdout

    Attributes
    ----------
    dumps_option: int
        An option parameter for orjson's dumps method
    pkgbases: list[OutputPackageBase]
        A list of OutputPackageBase instances to print (defaults to [])
    dependencies: list[Task] | None
        An optional list of Task instances that are run before this task (defaults to None)
    input_from_dependency: bool
        A boolean value indicating whether the Task derives its list of OutputPackageBase instances from a dependency
        Task (defaults to False)
    """

    def __init__(
        self,
        dumps_option: int,
        pkgbases: list[OutputPackageBase] | None = None,
        dependencies: list[Task] | None = None,
    ):
        """Initialize and instance of PrintOutputPackageBasesTask

        Parameters
        ----------
        dumps_option: int
            An option parameter for orjson's dumps method
        pkgbases: list[OutputPackageBase] | None
            An optional list of OutputPackageBase instances to print
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.input_from_dependency = False
        self.pkgbases: list[OutputPackageBase] = []

        if dependencies is not None:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, CreateOutputPackageBasesTask):
                    self.input_from_dependency = True

        debug("Initialize Task to print OutputPackageBase instances...")

        if not self.input_from_dependency:
            if pkgbases is None:
                raise RuntimeError("Pkgbases must be provided if not deriving input from another Task!")

            self.pkgbases = pkgbases

        self.dumps_option = dumps_option

    def do(self) -> ActionStateEnum:
        """Print OutputPackageBase instances in JSON representation

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise.
        """

        if self.input_from_dependency:
            for dependency in self.dependencies:
                if isinstance(dependency, CreateOutputPackageBasesTask):
                    match dependency.state:
                        case ActionStateEnum.SUCCESS:
                            self.pkgbases = dependency.pkgbases
                        case _:
                            self.state = ActionStateEnum.FAILED_DEPENDENCY
                            return self.state

        debug("Running Task to print OutputPackageBases in JSON format...")
        self.state = ActionStateEnum.STARTED_TASK

        for outputpackagebase in self.pkgbases:
            try:
                print(dumps(outputpackagebase.dict(), option=self.dumps_option).decode("utf-8"))
            except JSONEncodeError as e:
                info(e)
                return ActionStateEnum.FAILED_TASK

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the printing of OutputPackageBase instances

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            debug("Undoing Task to print OutputPackageBase instances not possible, as it never ran...")
            return self.state

        debug("Undoing Task to print OutputPackageBase instances...")

        if self.input_from_dependency:
            self.pkgbases.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class WriteOutputPackageBasesToTmpFileInDirTask(Task):
    """A Task to write instances of OutputPackageBase to temporary JSON files in a directory

    Attributes
    ----------
    filenames: list[Path] | None
        An optional list of Paths representing the OutputPackageBase instances that are written
    pkgbases: list[OutputPackageBase]
        A list of OutputPackageBase instances to write to file
    directory: Path
        A directory Path to write the files to
    """

    def __init__(
        self,
        directory: Path,
        dumps_option: int = ORJSON_OPTION,
        pkgbases: list[OutputPackageBase] | None = None,
        dependencies: list[Task] | None = None,
    ):
        """Initialize and instance of WriteOutputPackageBasesToTmpFileInDirTask

        Parameters
        ----------
        directory: Path
            A directory Path to write the files to
        dumps_option: int
            An option parameter for orjson's dumps method (defaults to repod.config.defaults.ORJSON_OPTION)
        pkgbases: list[OutputPackageBase] | None
            A list of OutputPackageBase instances to write to files
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.pkgbases = []
        self.input_from_dependency = False

        if dependencies is not None:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, CreateOutputPackageBasesTask):
                    self.input_from_dependency = True

        self.filenames: list[Path] = []
        self.directory = directory
        self.dumps_option = dumps_option

        if self.input_from_dependency:
            debug(
                "Creating Task to write instances of OutputPackageBase to a directory, "
                "using output from another Task..."
            )
        else:
            if pkgbases is None:
                raise RuntimeError("Pkgbases are required arguments, when not depending on another Task for input!")

            debug("Creating Task to write instances of OutputPackageBase to a directory...")
            self.pkgbases = pkgbases

    def do(self) -> ActionStateEnum:
        """Write instances of OutputPackageBase to temporary JSON files in a directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise.
        """

        pkgname_dir = self.directory / "pkgnames"

        self.state = ActionStateEnum.STARTED_TASK

        if self.input_from_dependency:
            debug(
                "Running Task to write OutputPackageBase instances to a management repository directory, "
                "using output from another Task..."
            )
            for dependency in self.dependencies:
                if isinstance(dependency, CreateOutputPackageBasesTask):
                    match dependency.state:
                        case ActionStateEnum.SUCCESS:
                            self.pkgbases = dependency.pkgbases
                        case _:
                            self.state = ActionStateEnum.FAILED_DEPENDENCY
                            return self.state
        else:
            debug("Running Task to write OutputPackageBase instances to a management repository directory...")

        pkgname_dir.mkdir(parents=True, exist_ok=True)

        for outputpackagebase in self.pkgbases:
            filename = self.directory / Path(f"{outputpackagebase.base}.json.tmp")  # type: ignore[attr-defined]
            self.filenames.append(filename)

            try:
                with open(filename, "wb") as output_file:
                    output_file.write(dumps(outputpackagebase.dict(), option=self.dumps_option))
            except (OSError, BlockingIOError, JSONEncodeError) as e:
                info(e)
                self.state = ActionStateEnum.FAILED_TASK
                return self.state

            target = self.directory / Path(f"{outputpackagebase.base}.json")  # type: ignore[attr-defined]
            for pkg in outputpackagebase.packages:  # type: ignore[attr-defined]
                symlink_path = pkgname_dir / Path(pkg.name + ".json.tmp")
                self.filenames.append(symlink_path)
                symlink_path.symlink_to(relative_to_shared_base(path_b=symlink_path, path_a=target))

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the writing of OutputPackageBase instances to temporary JSON files in a directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        debug(
            "Undoing Task to create an OutputPackageBase instance from a list of packages and "
            "writing it to a management repository directory..."
        )

        if self.state == ActionStateEnum.NOT_STARTED:
            info("Can not undo writing of OutputPackageBase to directory {self.directory}, as it never took place.")
            return self.state

        for filename in self.filenames:
            filename.unlink(missing_ok=True)
        self.filenames.clear()

        if self.input_from_dependency:
            self.pkgbases.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class MoveTmpFilesTask(Task):
    """A Task to move temporary files

    A backup of the destination (if it exists) is created prior to moving a file

    Attributes
    ----------
    paths: list[SourceDestination]
        A list of SourceDestination instances which represent the source and destination (plus additional data) for
        each file to be moved
    input_from_dependency: bool
        A boolean value indicating whether input is derived from a dependency Task (defaults to False)
    dependencies: list[Task] | None
        An optional list of Task instances that are run before this task (defaults to None)
    """

    def __init__(
        self,
        paths: list[list[Path]] | None = None,
        dependencies: list[Task] | None = None,
    ):
        """Initialize an instance of MoveTmpFilesTask

        If a WriteOutputPackageBasesToTmpFileInDirTask or WriteSyncDbsToTmpFilesInDirTask is provided as dependency
        Task, paths is derived from it (the input ordering of the Tasks is honored and the first match is used), else
        paths must be provided.

        Parameters
        ----------
        paths: list[list[Path]] | None
            An optional list of Path lists which represent the source and destination for each file to be moved
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.paths = []
        self.input_from_dependency = False

        if dependencies is not None:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, (WriteOutputPackageBasesToTmpFileInDirTask, WriteSyncDbsToTmpFilesInDirTask)):
                    self.input_from_dependency = True

        if self.input_from_dependency:
            debug("Creating Task to move a temporary file to a destination, using output from another Task...")
        else:
            if not paths:
                raise RuntimeError(
                    "A list of Path lists is a required argument, when not depending on another Task for input!"
                )
            if not all(len(path_list) == 2 for path_list in paths):
                raise RuntimeError("Path lists are required to be supplied in lists of length two!")

            debug(f"Creating Task to move {paths}...")
            self.paths = [
                SourceDestination(
                    source=path_list[0],
                    destination=path_list[1],
                    destination_backup=Path(str(path_list[1]) + ".bkp"),
                )
                for path_list in paths
            ]

    def do(self) -> ActionStateEnum:
        """Move files from their source to their destination (with potential backup of destination)

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise.
        """

        if self.input_from_dependency and len(self.dependencies) > 0:
            debug("Getting temporary files and their destinations from the output of another Task...")
            # NOTE: we can skip branch coverage here, as the only way to go through an empty list of dependencies is by
            # manipulating MoveTmpFilesTask.input_from_dependency after initialization
            for dependency in self.dependencies:  # pragma: no branch
                if isinstance(dependency, (WriteSyncDbsToTmpFilesInDirTask, WriteOutputPackageBasesToTmpFileInDirTask)):
                    match dependency.state:
                        case ActionStateEnum.SUCCESS if isinstance(
                            dependency, WriteOutputPackageBasesToTmpFileInDirTask
                        ):
                            try:
                                self.paths = [
                                    SourceDestination(
                                        source=filename,
                                        destination=Path(str(filename).replace(".tmp", "")),
                                        destination_backup=(Path(str(filename).replace(".tmp", "") + ".bkp")),
                                    )
                                    for filename in dependency.filenames
                                ]
                            except ValidationError as e:
                                info(e)
                                self.state = ActionStateEnum.FAILED_TASK
                                return self.state
                            break
                        case ActionStateEnum.SUCCESS if isinstance(dependency, WriteSyncDbsToTmpFilesInDirTask):
                            try:
                                self.paths = [
                                    SourceDestination(
                                        source=filename,
                                        destination=Path(str(filename).replace(".tmp", "")),
                                        destination_backup=(Path(str(filename).replace(".tmp", "") + ".bkp")),
                                    )
                                    for filename in [
                                        dependency.default_syncdb_path,
                                        dependency.default_syncdb_symlink_path,
                                        dependency.files_syncdb_path,
                                        dependency.files_syncdb_symlink_path,
                                    ]
                                ]
                            except ValidationError as e:
                                info(e)
                                self.state = ActionStateEnum.FAILED_TASK
                                return self.state
                            break
                        case _:
                            self.state = ActionStateEnum.FAILED_DEPENDENCY
                            return self.state

        debug(f"Running Task to move {self.paths}...")

        self.state = ActionStateEnum.STARTED_TASK

        for source_destination in self.paths:
            if source_destination.destination.exists():
                debug(f"Backing up {source_destination.destination} to {source_destination.destination_backup}...")
                try:
                    copy2(src=source_destination.destination, dst=source_destination.destination_backup)
                except Exception as e:
                    info(e)
                    self.state = ActionStateEnum.FAILED_TASK
                    return self.state
                source_destination.backup_done = True

            try:
                source_destination.source.rename(source_destination.destination)
            except Exception as e:
                info(e)
                self.state = ActionStateEnum.FAILED_TASK
                return self.state

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the moving of a file from source to destination

        Undo also all Tasks that have been run as a dependency.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state in [ActionStateEnum.NOT_STARTED, ActionStateEnum.FAILED_DEPENDENCY]:
            info(f"Can not undo moving of files {self.paths}, as it never took place.")
            self.state = ActionStateEnum.NOT_STARTED
            self.dependency_undo()
            return self.state

        for source_destination in self.paths:
            match (
                self.state,
                source_destination.source.exists(),
                source_destination.destination.exists(),
                source_destination.backup_done,
                source_destination.destination_backup.exists(),
            ):
                case (ActionStateEnum.SUCCESS_TASK, False, True, True, True) | (
                    ActionStateEnum.SUCCESS,
                    False,
                    True,
                    True,
                    True,
                ):
                    debug(f"Moving {source_destination.destination} back to {source_destination.source}...")
                    source_destination.destination.rename(source_destination.source)
                    debug(f"Moving {source_destination.destination_backup} back to {source_destination.destination}...")
                    source_destination.destination_backup.rename(source_destination.destination)
                    self.state = ActionStateEnum.NOT_STARTED
                case (ActionStateEnum.SUCCESS_TASK, False, True, False, False) | (
                    ActionStateEnum.SUCCESS,
                    False,
                    True,
                    False,
                    False,
                ):
                    debug(f"Moving {source_destination.destination} back to {source_destination.source}...")
                    source_destination.destination.rename(source_destination.source)
                    self.state = ActionStateEnum.NOT_STARTED
                case (ActionStateEnum.FAILED_TASK, True, False, False, False):
                    self.state = ActionStateEnum.NOT_STARTED
                case (ActionStateEnum.FAILED_TASK, True, True, True, True):
                    debug(
                        f"Removing backup {source_destination.destination_backup} of "
                        f" destination {source_destination.destination}..."
                    )
                    source_destination.destination_backup.unlink()
                    self.state = ActionStateEnum.NOT_STARTED
                case _:  # pragma: no cover
                    info(f"Can not undo moving of files {self.paths}!")
                    self.state = ActionStateEnum.FAILED_UNDO_TASK

        self.dependency_undo()
        return self.state


class FilesToRepoDirTask(Task):
    """A Task to copy files to a package pool directory and create symlinks for them in package repository directories

    Attributes
    ----------
    files: list[Path]
        A list of files to copy and create symlinks for
    file_type: RepoFileEnum
        An instance of RepoFileEnum, indicating what type of RepoFile to initialize
    settings: UserSettings | SystemSettings
        A instance of Settings to derive package_repo_dir and package_pool_dir from
    name: Path
        The name of a repository
    architecture: ArchitectureEnum | None
        The optional architecture of the target repository
    debug_repo: bool
        A boolean value indicating whether a debug repository is targeted
    staging_repo: bool
        A boolean value indicating whether a staging repository is targeted
    testing_repo: bool
        A boolean value indicating whether a testing repository is targeted
    repo_files: list[RepoFile]
        A a list of RepoFile instances that represent the files and their targets (defaults to [])
    """

    def __init__(
        self,
        files: list[Path],
        file_type: RepoFileEnum,
        settings: UserSettings | SystemSettings,
        name: Path,
        architecture: ArchitectureEnum | None,
        debug_repo: bool,
        staging_repo: bool,
        testing_repo: bool,
        dependencies: list[Task] | None = None,
    ):
        """Initialize an instance of FilesToRepoDirTask

        Parameters
        ----------
        files: list[Path]
            A list of files to copy and create symlinks for
        file_type: RepoFileEnum
            An instance of RepoFileEnum, indicating what type of RepoFile to initialize
        settings: UserSettings | SystemSettings
            A instance of Settings to derive package_repo_dir and package_pool_dir from
        name: Path
            The name of a repository
        architecture: ArchitectureEnum | None
            The optional architecture of the target repository
        debug_repo: bool
            A boolean value indicating whether a debug repository is targeted
        staging_repo: bool
            A boolean value indicating whether a staging repository is targeted
        testing_repo: bool
            A boolean value indicating whether a testing repository is targeted
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        debug(f"Creating Task to move {files} to repo {name} ({architecture})...")

        if dependencies is not None:
            self.dependencies = dependencies

        self.files = files
        self.file_type = file_type
        self.settings = settings
        self.name = name
        self.architecture = architecture
        self.debug = debug_repo
        self.staging = staging_repo
        self.testing = testing_repo
        self.repo_files: list[RepoFile] = []

    def do(self) -> ActionStateEnum:
        """Copy files to a package pool directory and create symlinks for them in a package repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise.
        """

        self.state = ActionStateEnum.STARTED_TASK

        debug(f"Running Task to move {self.files} to repo {self.name} ({self.architecture})...")

        try:
            package_repo_dir = self.settings.get_repo_path(
                repo_type=RepoDirTypeEnum.PACKAGE,
                name=self.name,
                architecture=self.architecture,
                debug=self.debug,
                staging=self.staging,
                testing=self.testing,
            )
            package_pool_dir = self.settings.get_repo_path(
                repo_type=RepoDirTypeEnum.POOL,
                name=self.name,
                architecture=self.architecture,
                debug=self.debug,
                staging=self.staging,
                testing=self.testing,
            )
        except RuntimeError as e:
            info(e)
            self.state = ActionStateEnum.FAILED_TASK
            return self.state

        for file_path in self.files:
            try:
                repo_file = RepoFile(
                    file_type=self.file_type,
                    file_path=package_pool_dir / file_path.name,
                    symlink_path=package_repo_dir / file_path.name,
                )
                self.repo_files.append(repo_file)
            except (ValidationError, RuntimeError) as e:
                info(e)
                self.state = ActionStateEnum.FAILED_TASK
                return self.state

            try:
                repo_file.copy_from(path=file_path)
                repo_file.link()
            except RepoManagementFileError as e:
                info(e)
                self.state = ActionStateEnum.FAILED_TASK
                return self.state

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the copying of files to a package pool directory and create symlinks for them in a package repository
        directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            info(
                f"Can not undo moving of packages {self.files} to repository {self.name} ({self.architecture}) "
                f"as it has not happened yet!"
            )
            self.dependency_undo()
            return self.state

        for repo_file in self.repo_files:
            repo_file.remove(force=True, unlink=True)
        self.repo_files.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class AddToRepoTask(Task):
    """Add package files to a repository

    Attributes
    ----------
    dependencies: list[Task]
        A list of Tasks that are dependencies of this one
    """

    def __init__(self, dependencies: list[Task]):
        """Initialize an instance of AddToRepoTask

        Parameters
        ----------
        dependencies: list[Task]
            A list of Tasks that are dependencies of this one
        """

        self.dependencies = dependencies

    def do(self) -> ActionStateEnum:
        """Run Task to add package files to a repository

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the adding of packages to a repository

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class WriteSyncDbsToTmpFilesInDirTask(Task):
    """A Task to write a repository's sync databases and their symlinks to temporary files in a directory

    Attributes
    ----------
    compression: CompressionTypeEnum
        A member of CompressionTypeEnum which is used as compression type for the repository sync databases
    desc_version: PackageDescVersionEnum
        A member of PackageDescVersionEnum which is used to set the PackageDesc version to write to file
    files_version: FilesVersionEnum
        A member of FilesVersionEnum which is used to set the PackageDesc version to write to file
    management_repo_dir: Path
        A Path to a directory in a management repository from which to read JSON files
    default_syncdb_path: Path
        A Path for the temporary default repository sync database
    files_syncdb_path: Path
        A Path for the temporary files repository sync database
    default_syncdb_symlink_path: Path
        A Path for the temporary symlink to the default repository sync database
    files_syncdb_symlink_path: Path
        A Path for the temporary symlink to the files repository sync database
    dependencies: list[Task] | None
        An optional list of Task lists which are executed before this Task (defaults to None)
    """

    def __init__(
        self,
        compression: CompressionTypeEnum,
        desc_version: PackageDescVersionEnum,
        files_version: FilesVersionEnum,
        management_repo_dir: Path,
        package_repo_dir: Path,
        dependencies: list[Task] | None = None,
    ):
        """Initialize an instance of WriteSyncDbsToTmpFilesInDirTask

        Parameters
        ----------
        compression: CompressionTypeEnum
            A member of CompressionTypeEnum which is used as compression type for the repository sync databases
        desc_version: PackageDescVersionEnum
            A member of PackageDescVersionEnum which is used to set the PackageDesc version to write to file
        files_version: FilesVersionEnum
            A member of FilesVersionEnum which is used to set the PackageDesc version to write to file
        management_repo_dir: Path
            A Path to a directory in a management repository from which to read JSON files
        package_repo_dir: Path
            A Path to a directory in a package repository to write files to
        dependencies: list[Task] | None
            An optional list of Task lists which are executed before this Task (defaults to None)
        """

        self.compression = compression
        self.desc_version = desc_version
        self.files_version = files_version
        self.management_repo_dir = management_repo_dir
        self.default_syncdb_path = package_repo_dir / Path(
            package_repo_dir.parent.name + CompressionTypeEnum.db_tar_suffix(compression_type=compression) + ".tmp"
        )
        self.default_syncdb_symlink_path = package_repo_dir / Path(package_repo_dir.parent.name + ".db.tmp")
        self.files_syncdb_path = package_repo_dir / Path(
            package_repo_dir.parent.name
            + CompressionTypeEnum.db_tar_suffix(compression_type=compression, files=True)
            + ".tmp"
        )
        self.files_syncdb_symlink_path = package_repo_dir / Path(package_repo_dir.parent.name + ".files.tmp")
        if dependencies:
            self.dependencies = dependencies

    def do(self) -> ActionStateEnum:
        """Run Task to write temporary repository sync databases to a package repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        self.state = ActionStateEnum.STARTED_TASK

        debug(
            f"Running Task to write temporary repository sync databases {self.default_syncdb_path} and "
            f"{self.files_syncdb_path}..."
        )

        try:
            default_sync_db = SyncDatabase(
                database=self.default_syncdb_path,
                database_type=RepoDbTypeEnum.DEFAULT,
                compression_type=self.compression,
                desc_version=self.desc_version,
                files_version=self.files_version,
            )
            files_sync_db = SyncDatabase(
                database=self.files_syncdb_path,
                database_type=RepoDbTypeEnum.FILES,
                compression_type=self.compression,
                desc_version=self.desc_version,
                files_version=self.files_version,
            )
        except ValidationError as e:
            info(e)
            self.state = ActionStateEnum.FAILED_TASK
            return self.state

        try:
            asyncio.run(default_sync_db.stream_management_repo(path=self.management_repo_dir))
            asyncio.run(files_sync_db.stream_management_repo(path=self.management_repo_dir))
        except (IsADirectoryError, RepoManagementFileNotFoundError) as e:
            info(e)
            self.state = ActionStateEnum.FAILED_TASK
            return self.state

        self.default_syncdb_symlink_path.symlink_to(
            Path(sub(r"\.tmp$", "", str(self.default_syncdb_path))).relative_to(self.default_syncdb_symlink_path.parent)
        )
        self.files_syncdb_symlink_path.symlink_to(
            Path(sub(r"\.tmp$", "", str(self.files_syncdb_path))).relative_to(self.files_syncdb_symlink_path.parent)
        )

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the writing of temporary repository sync databases in a package repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            info(
                f"Can not undo writing of temporary repository sync databases {self.default_syncdb_path} and "
                f"{self.files_syncdb_path}, as it has not happened yet!"
            )
            self.dependency_undo()
            return self.state

        for path in [
            self.files_syncdb_path,
            self.files_syncdb_symlink_path,
            self.default_syncdb_path,
            self.default_syncdb_symlink_path,
        ]:
            if not path.is_dir():
                path.unlink(missing_ok=True)

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class RemoveBackupFilesTask(Task):
    """A destructive(!) Task to remove backup files

    Attributes
    ----------
    paths: list[Path]
        A list of backup file paths to remove
    dependencies: list[Task] | None
        An optional list of Task lists which are executed before this Task (defaults to None)
    """

    def __init__(self, paths: list[Path] | None = None, dependencies: list[Task] | None = None):
        """Initialize an instance of RemoveBackupFilesTask

        If instances of MoveTmpFilesTask are provided in dependencies, paths is populated from them.

        Parameters
        ----------
        paths: list[Path] | None
            An optional list of Paths which represent the backup files to be removed
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.input_from_dependency: bool = False
        if dependencies:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, MoveTmpFilesTask):
                    self.input_from_dependency = True

        if self.input_from_dependency:
            debug("Creating Task to remove backup files, using output from another Task...")
            self.paths = []
        else:
            if not paths:
                raise RuntimeError("Paths must be provided if not depending on another Task for input!")

            debug(f"Creating Task to backup files {paths}...")
            self.paths = paths

    def do(self) -> ActionStateEnum:
        """Run Task to remove backup files

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        if self.input_from_dependency and len(self.dependencies) > 0:
            debug("Getting backup files from the output of another Task...")
            for dependency in self.dependencies:  # pragma: no branch
                if isinstance(dependency, MoveTmpFilesTask):
                    if dependency.state == ActionStateEnum.SUCCESS:
                        self.paths += [obj.destination_backup for obj in dependency.paths]
                    else:
                        self.state = ActionStateEnum.FAILED_DEPENDENCY
                        return self.state

        debug(f"Running Task to remove backup files {self.paths}...")
        self.state = ActionStateEnum.STARTED_TASK

        for path in self.paths:
            path.unlink(missing_ok=True)

        self.state = ActionStateEnum.SUCCESS_TASK

        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo Task for the removal of backup files

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            info(f"Can not undo removing of backup files {self.paths} as it has not happened yet!")
            self.dependency_undo()
            return self.state

        if self.input_from_dependency:
            self.paths.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class ConsolidateOutputPackageBasesTask(Task):
    """Task to compare OutputPackageBase instances with those in a management repository

    Attributes
    ----------
    pkgbases: list[OutputPackageBase]
        A list of OutputPackageBase instances to compare to those in a management repository directory
    directory: Path
        A Path to the directory in a management repository where to look for OutputPackageBases
    filenames: list[str]
        A list of package filenames associated with the OutputPackageBases in pkgbases
    package_names: list[str]
        A list of package names associated with the OutputPackageBases in pkgbases
    current_filenames: list[str]
        A list of package filenames associated with the pkgbases in directory, that match those in pkgbases
    current_package_names: list[str]
        A list of package names associated with the pkgbases in directory, that match those in pkgbases
    url_validation_settings: UrlValidationSettings | None
        An optional instance of UrlValidationSettings providing settings for validating the source URLs of pkgbases
        (defaults to None)
    """

    def __init__(
        self,
        directory: Path,
        url_validation_settings: UrlValidationSettings | None = None,
        pkgbases: list[OutputPackageBase] | None = None,
        dependencies: list[Task] | None = None,
    ):
        """Initialize an instance of ConsolidateOutputPackageBasesTask

        If instances of CreateOutputPackageBasesTask are provided in dependencies, pkgbases is populated from them.

        Parameters
        ----------
        directory: Path
            A Path to the directory in a management repository where to look for OutputPackageBases
        pkgbases: list[OutputPackageBase] | None
            An optional list of OutputPackageBase instances to compare to those in a management repository directory
        url_validation_settings: UrlValidationSettings | None
            An optional instance of UrlValidationSettings providing settings for validating the source URLs of pkgbases
            (defaults to None)
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.directory = directory
        if not self.directory or not self.directory.exists():
            raise RuntimeError("The provided directory must exist!")

        self.url_validation_settings = url_validation_settings
        self.input_from_dependency = False

        if dependencies:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, CreateOutputPackageBasesTask):
                    self.input_from_dependency = True

        if self.input_from_dependency:
            debug("Creating Task to compare OutputPackageBases, using output from another Task...")
            self.pkgbases = []
        else:
            if not pkgbases:
                raise RuntimeError("Pkgbases must be provided if not depending on another Task for input!")

            debug(
                "Creating Task to compare pkgbases "
                f"{[pkgbase.base for pkgbase in pkgbases]}..."  # type: ignore[attr-defined]
            )
            self.pkgbases = pkgbases

        self.filenames: list[str] = []
        self.package_names: list[str] = []
        self.current_filenames: list[str] = []
        self.current_package_names: list[str] = []

    def do(self) -> ActionStateEnum:
        """Run Task to compare OutputPackageBase instances with those in a management repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        if self.input_from_dependency and len(self.dependencies) > 0:
            debug("Getting pkgbases from the output of another Task...")
            for dependency in self.dependencies:  # pragma: no branch
                if isinstance(dependency, CreateOutputPackageBasesTask):
                    if dependency.state == ActionStateEnum.SUCCESS:
                        self.pkgbases = dependency.pkgbases
                    else:
                        self.state = ActionStateEnum.FAILED_DEPENDENCY
                        return self.state

        pkgbase_names = [pkgbase.base for pkgbase in self.pkgbases]  # type: ignore[attr-defined]
        self.filenames = [
            package.filename
            for package_list in [pkgbase.packages for pkgbase in self.pkgbases]  # type: ignore[attr-defined]
            for package in package_list
        ]
        self.package_names = [
            package.name
            for package_list in [pkgbase.packages for pkgbase in self.pkgbases]  # type: ignore[attr-defined]
            for package in package_list
        ]

        debug(f"Running Task to consolidate pkgbases {pkgbase_names}...")
        self.state = ActionStateEnum.STARTED_TASK

        current_pkgbases: list[OutputPackageBase] = []

        for name in pkgbase_names:
            current_pkgbase_file = self.directory / Path(name + ".json")
            if current_pkgbase_file.exists():
                try:
                    current_pkgbase = asyncio.run(OutputPackageBase.from_file(current_pkgbase_file))
                except RepoManagementFileError as e:
                    info(e)
                    self.state = ActionStateEnum.FAILED_TASK
                    return self.state
                self.current_filenames += [
                    package.filename for package in current_pkgbase.packages  # type: ignore[attr-defined]
                ]
                self.current_package_names += [
                    package.name for package in current_pkgbase.packages  # type: ignore[attr-defined]
                ]
                current_pkgbases.append(current_pkgbase)

        debug(f"Found new package filenames: {self.filenames}")
        debug(f"Found new package names: {self.package_names}")
        debug(f"Current package filenames: {self.current_filenames}")
        debug(f"Current package names: {self.current_package_names}")

        self.post_checks.append(
            SourceUrlCheck(
                new_pkgbases=self.pkgbases,
                current_pkgbases=current_pkgbases,
                url_validation_settings=self.url_validation_settings,
            )
        )
        self.post_checks.append(
            PkgbasesVersionUpdateCheck(new_pkgbases=self.pkgbases, current_pkgbases=current_pkgbases),
        )
        self.post_checks.append(
            PackagesNewOrUpdatedCheck(
                directory=self.directory,
                new_pkgbases=self.pkgbases,
                current_pkgbases=current_pkgbases,
            ),
        )

        self.state = ActionStateEnum.SUCCESS_TASK

        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo Task to consolidate OutputPackageBase instances with those from a management repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            info(
                "Can not undo consolidation of OutputPackageBases "
                f"{[pkgbase.base for pkgbase in self.pkgbases]} "  # type: ignore[attr-defined]
                "as it has not happened yet!"
            )
            self.dependency_undo()
            return self.state

        if self.input_from_dependency:
            self.pkgbases.clear()

        self.filenames.clear()
        self.package_names.clear()
        self.current_filenames.clear()
        self.current_package_names.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class RemoveManagementRepoSymlinksTask(Task):
    """Destructive Task to remove symlinks in a management repository directory

    Attributes
    ----------
    directory: Path
        A Path to the directory in a management repository
    names: list[str]
        A list of names, representing package in the management repository
    """

    def __init__(self, directory: Path, names: list[str] | None = None, dependencies: list[Task] | None = None):
        """Initialize an instance of RemoveManagementRepoSymlinksTask

        If instances of ConsolidateOutputPackageBasesTask are provided in dependencies, names is populated from them.

        Parameters
        ----------
        directory: Path
            A Path to the directory in a management repository
        names: list[str] | None
            An aoptional list of names, representing package in the management repository (defaults to None)
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.directory = directory
        if not self.directory or not self.directory.exists():
            raise RuntimeError("The provided directory must exist!")

        self.input_from_dependency = False

        if dependencies:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, ConsolidateOutputPackageBasesTask):
                    self.input_from_dependency = True

        if self.input_from_dependency:
            debug(
                "Creating Task to remove symlinks in a management repository directory, "
                "using output from another Task..."
            )
            self.names = []
        else:
            if not names:
                raise RuntimeError("Names must be provided if not depending on another Task for input!")

            debug(
                f"Creating Task to remove symlinks {', '.join([name for name in names])} "
                f"in repository directory {directory}..."
            )
            self.names = names

    def do(self) -> ActionStateEnum:
        """Run Task to remove symlinks in a management repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        if self.input_from_dependency and len(self.dependencies) > 0:
            debug("Getting pkgbases from the output of another Task...")
            for dependency in self.dependencies:  # pragma: no branch
                if isinstance(dependency, ConsolidateOutputPackageBasesTask):
                    if dependency.state == ActionStateEnum.SUCCESS:
                        self.names = [
                            name for name in dependency.current_package_names if name not in dependency.package_names
                        ]
                    else:
                        self.state = ActionStateEnum.FAILED_DEPENDENCY
                        return self.state

        for name in self.names:
            symlink = self.directory / f"pkgnames/{name}.json"
            debug(f"Removing symlink {symlink}...")
            symlink.unlink(missing_ok=True)

        self.state = ActionStateEnum.SUCCESS_TASK

        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo Task to remove symlinks from a management repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            info(
                "Can not undo removing of symlinks for packages "
                f"{', '.join([name for name in self.names])} "
                "as it has not happened yet!"
            )
            self.dependency_undo()
            return self.state

        if self.input_from_dependency:
            self.names.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class RemovePackageRepoSymlinksTask(Task):
    """Destructive Task to remove symlinks in a package repository directory

    This Task removes symlinks for package files and their accompanying signature files.

    Attributes
    ----------
    directory: Path
        A Path to the directory in a package repository
    filenames: list[str]
        A list of filename strings
    """

    def __init__(self, directory: Path, filenames: list[str] | None = None, dependencies: list[Task] | None = None):
        """Initialize an instance of RemovePackageRepoSymlinksTask

        If instances of ConsolidateOutputPackageBasesTask are provided in dependencies, filenames is populated from
        them.

        Parameters
        ----------
        directory: Path
            A Path to the directory in a package repository
        filenames: list[str] | None
            An optional list of filename strings (defaults to None)
        dependencies: list[Task] | None
            An optional list of Task instances that are run before this task (defaults to None)
        """

        self.directory = directory
        if not self.directory or not self.directory.exists():
            raise RuntimeError("The provided directory must exist!")

        self.input_from_dependency = False

        if dependencies:
            self.dependencies = dependencies
            for dependency in self.dependencies:
                if isinstance(dependency, ConsolidateOutputPackageBasesTask):
                    self.input_from_dependency = True

        if self.input_from_dependency:
            debug(
                "Creating Task to remove symlinks in a package repository directory, using output from another Task..."
            )
            self.filenames = []
        else:
            if not filenames:
                raise RuntimeError("Filenames must be provided if not depending on another Task for input!")

            debug(
                f"Creating Task to remove symlinks {', '.join([filename for filename in filenames])} "
                f"in package repository directory {directory}..."
            )
            self.filenames = filenames

    def do(self) -> ActionStateEnum:
        """Run Task to remove symlinks in a package repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        if self.input_from_dependency and len(self.dependencies) > 0:
            debug("Getting pkgbases from the output of another Task...")
            for dependency in self.dependencies:  # pragma: no branch
                if isinstance(dependency, ConsolidateOutputPackageBasesTask):
                    if dependency.state == ActionStateEnum.SUCCESS:
                        self.filenames = dependency.current_filenames
                    else:
                        self.state = ActionStateEnum.FAILED_DEPENDENCY
                        return self.state

        for filename in self.filenames:
            package_file = self.directory / filename
            signature_file = self.directory / f"{filename}.sig"
            debug(f"Removing symlink {package_file}...")
            package_file.unlink(missing_ok=True)
            debug(f"Removing symlink {signature_file}...")
            signature_file.unlink(missing_ok=True)

        self.state = ActionStateEnum.SUCCESS_TASK

        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo Task to remove symlinks from a package repository directory

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        if self.state == ActionStateEnum.NOT_STARTED:
            info(
                "Can not undo removing of symlinks "
                f"{', '.join([filename for filename in self.filenames])} "
                f"from package repository directory {str(self.directory)} as it has not happened yet!"
            )
            self.dependency_undo()
            return self.state

        if self.input_from_dependency:
            self.filenames.clear()

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state


class CleanupRepoTask(Task):
    """Cleanup files in a repository

    Attributes
    ----------
    dependencies: list[Task]
        A list of Tasks that are dependencies of this one
    """

    def __init__(self, dependencies: list[Task]):
        """Initialize an instance of AddToRepoTask

        Parameters
        ----------
        dependencies: list[Task]
            A list of Tasks that are dependencies of this one
        """

        self.dependencies = dependencies

    def do(self) -> ActionStateEnum:
        """Run Task to add package files to a repository

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS_TASK if the Task ran successfully,
            ActionStateEnum.FAILED_TASK otherwise
        """

        self.state = ActionStateEnum.SUCCESS_TASK
        return self.state

    def undo(self) -> ActionStateEnum:
        """Undo the adding of packages to a repository

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.NOT_STARTED if undoing the Task operation is successful,
            ActionStateEnum.FAILED_UNDO_DEPENDENCY if undoing of any of the dependency Tasks failed,
            ActionStateEnum.FAILED_UNDO_TASK otherwise
        """

        self.state = ActionStateEnum.NOT_STARTED
        self.dependency_undo()
        return self.state
