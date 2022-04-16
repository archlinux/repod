import io

from pydantic import BaseModel

from repo_management import defaults

from .common import Name


class RepoDbMemberType(BaseModel):
    """A model describing a single 'member_type' attribute, which is used to identify/ distinguish different types of
    repository database file types (e.g. 'desc' and 'files' files, which are contained in a repository database file).

    Attributes
    ----------
    member_type: defaults.RepoDbMemberType
        A member of the IntEnum defaults.RepoDbMemberType
    """

    member_type: defaults.RepoDbMemberType


class RepoDbMemberData(Name, RepoDbMemberType):
    """A model describing a set of attributes to provide the data of a 'desc' or 'files' file

    Attributes
    ----------
    name: str
        A package name
    member_type: defaults.RepoDbMemberType
        A member of the IntEnum defaults.RepoDbMemberType
    data: io.StringIO
        The contents of a 'desc' or 'files' file provided as a StringIO instance
    """

    data: io.StringIO

    class Config:
        arbitrary_types_allowed = True
