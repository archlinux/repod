import io
from typing import Dict, List, Set, Union

from repod import errors
from repod.common.enums import FieldTypeEnum
from repod.repo.package import (
    Files,
    PackageDesc,
    RepoDbMemberTypeEnum,
    get_desc_json_field_type,
    get_desc_json_keys,
    get_desc_json_name,
    get_files_json_field_type,
    get_files_json_keys,
    get_files_json_name,
)


async def file_data_to_model(
    data: io.StringIO, data_type: RepoDbMemberTypeEnum, name: str
) -> Union[Files, PackageDesc]:
    """Read the contents of a 'desc' or 'files' file (provided as io.StringIO) and convert it to a pydantic model

    Parameters
    ----------
    data: io.StringIO
        A buffered I/O that represents a 'desc' file
    data_type: RepoDbMemberTypeEnum
        An IntEnum specifying which type of data is converted (e.g. that of a 'desc' file or that of a 'files' file)
    name: str
        The name of the package, that the data belongs to

    Raises
    ------
    errors.RepoManagementFileError
        If an unknown file is attempted to be read
    errors.RepoManagementValidationError
        If a pydantic.error_wrappers.ValidationError is raised (e.g. due to a missing attribute) or if a ValueError is
        raised when converting data (e.g. when calling _desc_data_line_to_dicts())

    Returns
    -------
    Union[PackageDesc, Files]
        A pydantic model, representing a 'desc' or a 'files' entry of a repository sync database
    """

    current_header = ""
    current_type: FieldTypeEnum
    int_types: Dict[str, int] = {}
    keys: Set[str]
    string_types: Dict[str, str] = {}
    string_list_types: Dict[str, List[str]] = {}

    match data_type:
        case RepoDbMemberTypeEnum.DESC:
            keys = get_desc_json_keys()
        case RepoDbMemberTypeEnum.FILES:
            keys = get_files_json_keys()
        case _:
            raise errors.RepoManagementFileError(
                f"Unknown file type encountered while attempting to read data for package '{name}' "
                "from a repository sync database."
            )

    for line in data:
        line = line.strip()
        if not line:
            continue

        if line in keys:
            match data_type:
                case RepoDbMemberTypeEnum.DESC:
                    current_header = get_desc_json_name(key=line)
                    current_type = get_desc_json_field_type(line)
                case RepoDbMemberTypeEnum.FILES:
                    current_header = get_files_json_name(key=line)
                    current_type = get_files_json_field_type(line)
                case _:  # pragma: no cover
                    pass
            # FIXME: find better way to provide a default (None or empty list for STRING_LIST as they all are
            # Optional[List[str]]
            if current_header and current_type == FieldTypeEnum.STRING_LIST:
                string_list_types[current_header] = []

            continue

        if current_header:
            try:
                match current_type:
                    case FieldTypeEnum.STRING_LIST:
                        string_list_types[current_header] += [line]
                    case FieldTypeEnum.STRING:
                        string_types[current_header] = line
                    case FieldTypeEnum.INT:
                        int_types[current_header] = int(line)
                    case _:  # pragma: no cover
                        pass
            except ValueError as e:
                raise errors.RepoManagementValidationError(
                    f"An error occured while attempting to cast values for the package '{name}':\n"
                    f"\n{data.getvalue()}\n{e}"
                )

    model: Union[PackageDesc, Files]

    match data_type:
        case RepoDbMemberTypeEnum.DESC:
            desc_dict: Dict[str, Union[int, str, List[str]]] = {**int_types, **string_types, **string_list_types}
            try:
                model = PackageDesc.from_dict(desc_dict)
            except errors.RepoManagementValidationError as e:
                raise errors.RepoManagementValidationError(
                    f"An error occured while validating the 'desc' file of package '{name}':\n"
                    f"\n{data.getvalue()}\n{e}"
                )
        case RepoDbMemberTypeEnum.FILES:
            try:
                model = Files.from_dict(data=string_list_types)
            except errors.RepoManagementValidationError as e:
                raise errors.RepoManagementValidationError(
                    f"An error occured while validating the 'files' file of package '{name}':\n"
                    f"\n{data.getvalue()}\n{e}"
                )
        case _:  # pragma: no cover
            pass

    return model
