from pathlib import Path
from typing import Union

from repod.repo.management import (  # noqa: F401
    Files,
    OutputPackage,
    OutputPackageBase,
    PackageDesc,
)
from repod.repo.management import export_schemas as management_export_schemas
from repod.repo.package import (  # noqa: F401
    RepoDbMemberTypeEnum,
    RepoDbTypeEnum,
    SyncDatabase,
)
from repod.repo.package import export_schemas as package_export_schemas
from repod.repo.package import (  # noqa: F401
    get_desc_json_field_type,
    get_desc_json_keys,
    get_desc_json_name,
    get_files_json_field_type,
    get_files_json_keys,
    get_files_json_name,
)


def export_schemas(output: Union[Path, str]) -> None:
    """Export the JSON schema files of the repod.repo package to a directory

    Parameters
    ----------
    output: Path
        A directory to write the JSON schema files to
    """

    management_export_schemas(output=output)
    package_export_schemas(output=output)
