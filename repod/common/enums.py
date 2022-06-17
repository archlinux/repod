from enum import Enum, IntEnum


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
