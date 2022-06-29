from pathlib import Path
from typing import Union

from .files import export_schemas as files_export_schemas
from .repo import export_schemas as repo_export_schemas


def export_schemas(output: Union[Path, str]) -> None:
    """Export the JSON schema files of repod to a directory

    Parameters
    ----------
    output: Path
        A directory to write the JSON schema files to
    """

    files_export_schemas(output=output)
    repo_export_schemas(output=output)
