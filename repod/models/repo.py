from __future__ import annotations

import io
from enum import IntEnum
from typing import Dict, Set, Tuple

from pydantic import BaseModel

from repo_management.errors import RepoManagementFileError

from .common import Name


class FieldTypeEnum(IntEnum):
    """An IntEnum to distinguish the types of different entries in a 'desc' or 'files' file contained in repository
    sync databases.

    This information is required for being able to properly parse the data and have functioning typing.

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


DESC_JSON: Dict[str, Tuple[str, FieldTypeEnum]] = {
    "%BASE%": ("base", FieldTypeEnum.STRING),
    "%VERSION%": ("version", FieldTypeEnum.STRING),
    "%MAKEDEPENDS%": ("makedepends", FieldTypeEnum.STRING_LIST),
    "%CHECKDEPENDS%": ("checkdepends", FieldTypeEnum.STRING_LIST),
    "%FILENAME%": ("filename", FieldTypeEnum.STRING),
    "%NAME%": ("name", FieldTypeEnum.STRING),
    "%DESC%": ("desc", FieldTypeEnum.STRING),
    "%GROUPS%": ("groups", FieldTypeEnum.STRING_LIST),
    "%CSIZE%": ("csize", FieldTypeEnum.INT),
    "%ISIZE%": ("isize", FieldTypeEnum.INT),
    "%MD5SUM%": ("md5sum", FieldTypeEnum.STRING),
    "%SHA256SUM%": ("sha256sum", FieldTypeEnum.STRING),
    "%PGPSIG%": ("pgpsig", FieldTypeEnum.STRING),
    "%URL%": ("url", FieldTypeEnum.STRING),
    "%LICENSE%": ("license", FieldTypeEnum.STRING_LIST),
    "%ARCH%": ("arch", FieldTypeEnum.STRING),
    "%BUILDDATE%": ("builddate", FieldTypeEnum.INT),
    "%PACKAGER%": ("packager", FieldTypeEnum.STRING),
    "%REPLACES%": ("replaces", FieldTypeEnum.STRING_LIST),
    "%CONFLICTS%": ("conflicts", FieldTypeEnum.STRING_LIST),
    "%PROVIDES%": ("provides", FieldTypeEnum.STRING_LIST),
    "%DEPENDS%": ("depends", FieldTypeEnum.STRING_LIST),
    "%OPTDEPENDS%": ("optdepends", FieldTypeEnum.STRING_LIST),
    "%BACKUP%": ("backup", FieldTypeEnum.STRING_LIST),
}

FILES_JSON: Dict[str, Tuple[str, FieldTypeEnum]] = {"%FILES%": ("files", FieldTypeEnum.STRING_LIST)}


class RepoDbMemberTypeEnum(IntEnum):
    """An IntEnum to distinguish different types of files in a repository sync database.

    Attributes
    ----------
    UNKNOWN: int
        An unsupported file of unknown type
    DESC: int
        A 'desc' description file of a package
    FILES: int
        A 'files' file of a package
    """

    UNKNOWN = 0
    DESC = 1
    FILES = 2


class RepoDbTypeEnum(IntEnum):
    """An IntEnum to distinguish types of binary repository database files

    Attributes
    ----------
    DEFAULT: int
        Use this to identify .db files
    FILES: int
        Use this to identify .files files
    """

    DEFAULT = 0
    FILES = 2


class RepoDbMemberType(BaseModel):
    """A model describing a single 'member_type' attribute, which is used to identify/ distinguish different types of
    repository database file types (e.g. 'desc' and 'files' files, which are contained in a repository database file).

    Attributes
    ----------
    member_type: RepoDbMemberTypeEnum
        A member of RepoDbMemberTypeEnum
    """

    member_type: RepoDbMemberTypeEnum


class RepoDbMemberData(Name, RepoDbMemberType):
    """A model describing a set of attributes to provide the data of a 'desc' or 'files' file

    Attributes
    ----------
    name: str
        A package name
    member_type: RepoDbMemberTypeEnum
        A member of RepoDbMemberTypeEnum
    data: io.StringIO
        The contents of a 'desc' or 'files' file provided as a StringIO instance
    """

    data: io.StringIO

    class Config:
        arbitrary_types_allowed = True


def get_desc_json_keys() -> Set[str]:
    """Get the keys of repo_management.models.repo.DESC_JSON

    Returns
    -------
    Set[str]
        A set of strings representing the keys of repo_management.models.repo.DESC_JSON
    """

    return set(DESC_JSON.keys())


def get_desc_json_name(key: str) -> str:
    """Get the JSON name of a given key from the definition in repo_management.models.repo.DESC_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repo_management.models.repo.DESC_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The JSON name of a given 'desc' file identifier provided by key
    """

    try:
        return DESC_JSON[key][0]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'desc' file identifier.")


def get_desc_json_field_type(key: str) -> FieldTypeEnum:
    """Get the FieldTypeEnum of a given key from the definition in repo_management.models.repo.DESC_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repo_management.models.repo.DESC_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The FieldTypeEnum of a given 'desc' file identifier provided by key
    """

    try:
        return DESC_JSON[key][1]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'desc' file identifier.")


def get_files_json_keys() -> Set[str]:
    """Get the keys of repo_management.models.repo.FILES_JSON

    Returns
    -------
    Set[str]
        A set of strings representing the keys of repo_management.models.repo.FILES_JSON
    """

    return set(FILES_JSON.keys())


def get_files_json_name(key: str) -> str:
    """Get the JSON name of a given key from the definition in repo_management.models.repo.FILES_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repo_management.models.repo.FILES_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The JSON name of a given 'files' file identifier provided by key
    """

    try:
        return FILES_JSON[key][0]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'files' file identifier.")


def get_files_json_field_type(key: str) -> FieldTypeEnum:
    """Get the FieldTypeEnum of a given key from the definition in repo_management.models.repo.FILES_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repo_management.models.repo.FILES_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The FieldTypeEnum of a given 'desc' file identifier provided by key
    """

    try:
        return FILES_JSON[key][1]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'files' file identifier.")
