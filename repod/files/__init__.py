from pathlib import Path

from repod.files.buildinfo import BuildInfo  # noqa: F401
from repod.files.buildinfo import export_schemas as buildinfo_export_schemas
from repod.files.common import extract_file_from_tarfile, open_tarfile  # noqa: F401
from repod.files.mtree import MTree, MTreeEntry  # noqa: F401
from repod.files.mtree import export_schemas as mtree_export_schemas
from repod.files.package import Package  # noqa: F401
from repod.files.package import export_schemas as package_export_schemas
from repod.files.pkginfo import PkgInfo  # noqa: F401
from repod.files.pkginfo import export_schemas as pkginfo_export_schemas
from repod.files.srcinfo import PkgBaseSection, PkgNameSection, SrcInfo  # noqa: F401
from repod.files.srcinfo import export_schemas as srcinfo_export_schemas


def export_schemas(output: Path | str) -> None:
    """Export the JSON schema files of the repod.files package to a directory

    Parameters
    ----------
    output: Path
        A directory to write the JSON schema files to
    """

    buildinfo_export_schemas(output=output)
    mtree_export_schemas(output=output)
    package_export_schemas(output=output)
    pkginfo_export_schemas(output=output)
    srcinfo_export_schemas(output=output)
