from __future__ import annotations

import io
import re
import tarfile
from typing import AsyncIterator

from repod.files.common import extract_file_from_tarfile, open_tarfile  # noqa: F401
from repod.files.package import Package  # noqa: F401
from repod.repo.package import RepoDbMemberData, RepoDbMemberTypeEnum


async def _extract_db_member_package_name(name: str) -> str:
    """Extract and return the package name from a repository database member name

    Parameters
    ----------
    name: str
        The name of a member of a repository database (i.e. one of tarfile.Tarfile.getnames())

    Returns
    str
        The package name extracted from name
    """

    return "".join(re.split("(-)", re.sub("(/desc|/files)$", "", name))[:-4])


async def _db_file_member_as_model(
    db_file: tarfile.TarFile, regex: str = "(/desc|/files)$"
) -> AsyncIterator[RepoDbMemberData]:
    """Iterate over the members of a database file, represented by an instance of tarfile.TarFile and yield the members
    as instances of RepoDbMemberData

    The method filters the list of evaluated members using a regular expression. Depending on member name one of
    RepoDbMemberTypeEnum is chosen.

    Parameters
    ----------
    tarfile.TarFile
        An instance of TarFile representing a repository database
    regex: str
        A regular expression used to filter the names of the members contained in db_file (defaults to
        '(/desc|/files)$')
    """

    for name in [name for name in db_file.getnames() if re.search(regex, name)]:
        file_type = RepoDbMemberTypeEnum.UNKNOWN
        if re.search("(/desc)$", name):
            file_type = RepoDbMemberTypeEnum.DESC
        if re.search("(/files)$", name):
            file_type = RepoDbMemberTypeEnum.FILES

        yield RepoDbMemberData(
            member_type=file_type,
            name=await _extract_db_member_package_name(name=name),
            data=io.StringIO(
                io.BytesIO(
                    db_file.extractfile(name).read(),  # type: ignore[union-attr]
                )
                .read()
                .decode("utf-8"),
            ),
        )
