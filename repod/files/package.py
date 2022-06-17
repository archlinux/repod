from __future__ import annotations

from logging import debug
from pathlib import Path
from typing import Union

from pydantic import BaseModel

from repod.errors import RepoManagementFileError
from repod.files.buildinfo import BuildInfo
from repod.files.common import (  # noqa: F401
    extract_file_from_tarfile,
    names_in_tarfile,
    open_tarfile,
)
from repod.files.mtree import MTree
from repod.files.pkginfo import PkgInfo

PACKAGE_VERSIONS = {
    1: {
        "required": {".BUILDINFO", ".MTREE", ".PKGINFO"},
    },
}


class Package(BaseModel):
    """Package representation

    This is a template class and (apart from its class methods) should not be used directly. Instead instatiate one of
    the classes derived from it.
    """

    @classmethod
    async def from_file(cls, path: Path) -> Package:
        package_version = 0

        debug(f"Opening package file {path} for reading...")
        with open_tarfile(path) as tarfile:
            for version in range(len(PACKAGE_VERSIONS), 0, -1):
                debug(f"Testing data against Package version {version}...")
                if names_in_tarfile(tarfile=tarfile, names=PACKAGE_VERSIONS[version]["required"]):
                    debug(f"Package version {version} matches provided data!")
                    package_version = version
                    break

            match package_version:
                case 1:
                    return PackageV1(
                        buildinfo=BuildInfo.from_file(
                            data=await extract_file_from_tarfile(  # type: ignore[arg-type]
                                tarfile=tarfile,
                                file=".BUILDINFO",
                                as_stringio=True,
                            )
                        ),
                        mtree=MTree.from_file(
                            data=await extract_file_from_tarfile(  # type: ignore[arg-type]
                                tarfile=tarfile,
                                file=".MTREE",
                                as_stringio=True,
                                gzip_compressed=True,
                            ),
                        ),
                        pkginfo=PkgInfo.from_file(
                            data=await extract_file_from_tarfile(  # type: ignore[arg-type]
                                tarfile=tarfile,
                                file=".PKGINFO",
                                as_stringio=True,
                            ),
                        ),
                    )
                case _:
                    raise RepoManagementFileError(
                        f"The provided file {path} does not match any known package versions!"
                    )


class PackageV1(Package):
    """Package representation version 1

    Attributes
    ----------
    buildinfo: BuildInfo
        A .BUILDINFO file representation
    mtree: MTree
        An .MTREE file representation
    pkginfo: PkgInfo
        A .PKGINFO file representation
    """

    buildinfo: BuildInfo
    mtree: MTree
    pkginfo: PkgInfo


def export_schemas(output: Union[Path, str]) -> None:
    """Export the JSON schema of selected pydantic models to an output directory

    Parameters
    ----------
    output: Path
        A path to which to output the JSON schema files

    Raises
    ------
    RuntimeError
        If output is not an existing directory
    """

    classes = [PackageV1]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
