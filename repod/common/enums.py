from __future__ import annotations

from enum import Enum, IntEnum, IntFlag, auto
from typing import List


class ArchitectureEnum(Enum):
    """An Enum to distinguish different CPU architectures

    Attributes
    ----------
    AARCH64: "aarch64"
        The aarch64 CPU architecture
    ANY: "any"
        Any CPU architecture
    ARM: "arm"
        The arm CPU architecture
    ARMV6H: "armv6h"
        The armv6h CPU architecture
    ARMV7H: "armv7h"
        The armv7h CPU architecture
    I486: "i486"
        The i486 CPU architecture
    I686: "i686"
        The i686 CPU architecture
    PENTIUM4: "pentium4"
        The pentium4 CPU architecture
    RISCV32: "riscv32"
        The risv32 CPU architecture
    RISCV64: "riscv64"
        The risv64 CPU architecture
    X86_64: "x86_64"
        The x86_64 CPU architecture
    X86_64_V2: "x86_64_v2"
        The x86_64_v2 CPU architecture
    X86_64_V3: "x86_64_v3"
        The x86_64_v3 CPU architecture
    X86_64_V4: "x86_64_v4"
        The x86_64_v4 CPU architecture
    """

    AARCH64 = "aarch64"
    ANY = "any"
    ARM = "arm"
    ARMV6H = "armv6h"
    ARMV7H = "armv7h"
    I486 = "i486"
    I686 = "i686"
    PENTIUM4 = "pentium4"
    RISCV32 = "riscv32"
    RISCV64 = "riscv64"
    X86_64 = "x86_64"
    X86_64_V2 = "x86_64_v2"
    X86_64_V3 = "x86_64_v3"
    X86_64_V4 = "x86_64_v4"

    @classmethod
    def as_or_regex(cls) -> str:
        """Return the members of ArchitectureEnum formatted as an "or" concatenated string

        Returns
        -------
        str
            The members of ArchitectureEnum formatted as an "or" concatenated string
        """

        return r"|".join(arch.value for arch in cls)


class FieldTypeEnum(IntEnum):
    """An IntEnum to distinguish the different types of entries in a file

    Attributes
    ----------
    STRING: int
        An entry of type 'str'
    INT: int
        An entry of typoe 'int'
    STRING_LIST: int
        An entry of type 'List[str]'
    """

    STRING = 0
    INT = 1
    STRING_LIST = 2
    KEY_VALUE_LIST = 3


class CompressionTypeEnum(Enum):
    """An Enum to distinguish different compression types of a tar file

    The member values represents the name of possible file suffixes (without leading dot)

    Attributes
    ----------
    NONE: ""
        No compression
    BZIP2: "bz2"
        The bzip2 compression
    GZIP: "gz"
        The gzip compression
    LZMA: "xz"
        The lzma compression
    ZSTANDARD: "zst"
        The zstandard compression
    """

    NONE = ""
    BZIP2 = "bz2"
    GZIP = "gz"
    LZMA = "xz"
    ZSTANDARD = "zst"

    @classmethod
    def from_string(cls, input_: str) -> CompressionTypeEnum:
        """Return a CompressionTypeEnum member based on an input string

        Parameters
        ----------
        input_: str
            A string representing one of the CompressionTypeEnum members. Valid options are "none", "bzip2", "bz2",
            "gzip", "gz", "lzma", "xz", "zstandard" and "zst"

        Raises
        ------
        RuntimeError
            If an invalid input is provided

        Returns
        -------
        CompressionTypeEnum
            A CompressionTypeEnum member that matches input_
        """

        match input_:
            case "none":
                return CompressionTypeEnum.NONE
            case "bzip2" | "bz2":
                return CompressionTypeEnum.BZIP2
            case "gzip" | "gz":
                return CompressionTypeEnum.GZIP
            case "lzma" | "xz":
                return CompressionTypeEnum.LZMA
            case "zstandard" | "zst":
                return CompressionTypeEnum.ZSTANDARD
            case _:
                raise RuntimeError(f"The provided compression type {input_} is not valid!")

    @classmethod
    def db_tar_suffix(cls, compression_type: CompressionTypeEnum, files: bool = False) -> str:
        """Return a member of CompressionTypeEnum formated as the file suffix for a default or files repository sync
        database

        Parameters
        ----------
        compression_type: CompressionTypeEnum
            A member of CompressionTypeEnum to return the tar suffix for
        files: bool
            Whether to return the tar suffix for a files database (defaults to False)

        Returns
        -------
        str
            A member of CompressionTypeEnum formated as the file suffix for a default repository sync database
        """

        return (
            f".{'files' if files else 'db'}.tar." + compression_type.value
            if len(compression_type.value) > 0
            else f".{'files' if files else 'db'}.tar" + compression_type.value
        )

    @classmethod
    def as_db_file_suffixes(cls) -> List[str]:
        """Return the members of CompressionTypeEnum formated in a list of strings reprenting all possible suffix
        permutations for a default repository sync database

        Returns
        -------
        List[str]
            A list of strings representing all possible permutations of file suffixes for a default repository sync
            database
        """

        return [".db", ".db.tar"] + [".db.tar." + name.value for name in cls if len(name.value) > 0]

    @classmethod
    def as_files_file_suffixes(cls) -> List[str]:
        """Return the members of CompressionTypeEnum formated in a list of strings reprenting all possible suffix
        permutations for a files repository sync database

        Returns
        -------
        List[str]
            A list of strings representing all possible permutations of file suffixes for a files repository sync
            database
        """

        return [".files", ".files.tar"] + [".files.tar." + name.value for name in cls if len(name.value) > 0]


class FilesVersionEnum(IntEnum):
    """An IntEnum to distinguish different version of Files

    Attributes
    ----------
    DEFAULT: int
        The default Files version
    ONE: int
        The first Files version
    """

    DEFAULT = 1
    ONE = 1


class OutputPackageVersionEnum(IntEnum):
    """An IntEnum to distinguish different version of OutputPackage

    Attributes
    ----------
    DEFAULT: int
        The default OutputPackage version
    ONE: int
        The first OutputPackage version
    """

    DEFAULT = 1
    ONE = 1


class PackageDescVersionEnum(IntEnum):
    """An IntEnum to distinguish different version of PackageDesc

    Attributes
    ----------
    DEFAULT: int
        The default PackageDesc version
    ONE: int
        The first PackageDesc version
    TWO: int
        The second PackageDesc version
    """

    DEFAULT = 1
    ONE = 1
    TWO = 2


class PkgVerificationTypeEnum(Enum):
    """An Enum to distinguish different package signature verification implementations

    Attributes
    ----------
    PACMANKEY: str
        An implementation based on pacman-key --verify
    """

    PACMANKEY = "pacman-key"


class PkgTypeEnum(Enum):
    """An Enum to distinguish different package types

    The member values represents the name of a possible repod.files.pkginfo.PkgType value

    Attributes
    ----------
    PKG: str
        A default package
    DEBUG: str
        A debug package
    SOURCE: str
        A source package
    SPLIT: str
        A split package
    """

    PKG = "pkg"
    DEBUG = "debug"
    SOURCE = "src"
    SPLIT = "split"


class RepoFileEnum(IntEnum):
    """An Enum to distinguish different types of RepoFiles

    Attributes
    ----------
    PACKAGE: int
        A package file
    PACKAGE_SIGNATURE: int
        A package signature file
    """

    PACKAGE = 0
    PACKAGE_SIGNATURE = 1


class RepoDirTypeEnum(Enum):
    """An Enum to distinguish different types of repository directories

    Attributes
    ----------
    MANAGEMENT: str
        A management repository directory
    PACKAGE: str
        A package repository directory
    POOL: str
        A pool directory directory
    """

    MANAGEMENT = "management"
    PACKAGE = "package"
    POOL = "pool"


class SettingsTypeEnum(Enum):
    """An Enum to distinguish different Settings types

    Attributes
    ----------
    USER: str
        User Settings
    SYSTEM: str
        System Settings
    """

    USER = "user"
    SYSTEM = "system"


def tar_compression_types_for_filename_regex() -> str:
    """Return the members of CompressionTypeEnum formatted for use in the FILENAME regular expression

    Returns
    -------
    str
        The members of CompressionTypeEnum formatted as an "or" concatenated string (including a leading empty match for
        no compression)
    """

    return r"|".join([type_.value for type_ in CompressionTypeEnum]).replace("|", r"|\.")


class ActionStateEnum(IntFlag):
    """An Enum to distinguish different states in Checks and Tasks

    Attributes
    ----------
    NOT_STARTED: int
        An action is not started
    STARTED: int
        An action is started
    STARTED_TASK: int
        An action is started and is a Task
    FAILED: int
        An action is failed
    FAILED_DEPENDENCY: int
        An action's dependency is failed
    FAILED_PRE_CHECK: int
        An action is failed and is a pre Check
    FAILED_POST_CHECK: int
        An action is failed and is a post Check
    FAILED_TASK: int
        An action is failed and is a Task
    FAILED_UNDO_DEPENDENCY: int
        An action is failed and is an undo Task of a dependency
    FAILED_UNDO_TASK: int
        An action is failed and is an undo Task
    SUCCESS: int
        An action is successful
    SUCCESS_TASK: int
        An action is successful and is a Task
    """

    NOT_STARTED = auto()
    STARTED = auto()
    STARTED_TASK = auto()
    FAILED = auto()
    FAILED_DEPENDENCY = auto()
    FAILED_PRE_CHECK = auto()
    FAILED_POST_CHECK = auto()
    FAILED_TASK = auto()
    FAILED_UNDO_DEPENDENCY = auto()
    FAILED_UNDO_TASK = auto()
    SUCCESS = auto()
    SUCCESS_TASK = auto()
