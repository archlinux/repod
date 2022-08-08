from __future__ import annotations

from enum import Enum, IntEnum
from typing import List


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
    def as_db_file_suffixes(cls) -> List[str]:
        """Return the members of CompressTypeEnum formated in a list of strings reprenting all possible suffix
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
        """Return the members of CompressTypeEnum formated in a list of strings reprenting all possible suffix
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

    The member values represents the name of a possible repod.files.buildinfo.PkgType value

    Attributes
    ----------
    PKG: str
        A default package
    DEBUG: str
        A debug package
    """

    PKG = "pkg"
    DEBUG = "debug"


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


class RepoTypeEnum(Enum):
    """An Enum to distinguish different types of repositories

    Attributes
    ----------
    MANAGEMENT: str
        A management repository
    PACKAGE: str
        A package repository
    """

    MANAGEMENT = "management"
    PACKAGE = "package"


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


def pkg_types_for_pkgtype_regex() -> str:
    """Return the members of PkgTypeEnum formatted for use in the PKGTYPE regular expression

    Returns
    -------
    str
        The members of PkgTypeEnum formatted as an "or" concatenated string, which matches the values of all members.
    """

    return r"|".join([type_.value for type_ in PkgTypeEnum])


def tar_compression_types_for_filename_regex() -> str:
    """Return the members of CompressionTypeEnum formatted for use in the FILENAME regular expression

    Returns
    -------
    str
        The members of CompressionTypeEnum formatted as an "or" concatenated string (including a leading empty match for
        no compression)
    """

    return r"|".join([type_.value for type_ in CompressionTypeEnum]).replace("|", r"|\.")
