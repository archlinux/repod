import io
from typing import Dict, List, Optional, Union

from repo_management import defaults, models


def _files_data_to_model(data: io.StringIO) -> models.Files:
    """Read the contents of a 'files' file (represented as an instance of
    io.StringIO) and convert it to a pydantic model

    Closes the io.StringIO upon error or before returning the dict

    Parameters
    ----------
    data: io.StringIO
        A buffered I/O that represents a 'files' file

    Raises
    ------
    RuntimeError
        If the 'files' file is missing its %FILES% header

    Returns
    -------
    models.Files
        A pydantic model representing the list of files of a package
    """

    name = str(defaults.FILES_JSON["%FILES%"]["name"])
    output: Dict[str, List[str]] = {name: []}
    line_counter = 0

    for line in data:
        line = line.strip()
        if line_counter == 0 and line not in defaults.FILES_JSON.keys():
            data.close()
            raise RuntimeError(f"The 'files' data misses its header: '{line}' was provided.")
        if line_counter > 0 and line not in defaults.FILES_JSON.keys() and line:
            output[name] += [line]
        line_counter += 1

    data.close()
    return models.Files(**output)


def _desc_data_to_model(data: io.StringIO) -> models.PackageDesc:
    """Read the contents of a 'desc' file (represented as an instance of io.StringIO) and convert it to a pydantic model

    Parameters
    ----------
    data: io.StringIO
        A buffered I/O that represents a 'desc' file

    Raises
    ------
    ValueError
        If a string is provided for a field of type int, that can not be cast to type int
    pydantic.error_wrappers.ValidationError
        If a required field is missing

    Returns
    -------
    models.PackageDesc
        A pydantic model, representing a package
    """

    current_header = ""
    current_type: defaults.FieldType
    int_types: Dict[str, int] = {}
    string_types: Dict[str, str] = {}
    string_list_types: Dict[str, List[str]] = {}

    for line in data:
        line = line.strip()
        if not line:
            continue

        if line in defaults.DESC_JSON.keys():
            current_header = str(defaults.DESC_JSON[line]["name"])
            current_type = defaults.FieldType(defaults.DESC_JSON[line]["type"])
            continue

        if current_header:
            if current_type == defaults.FieldType.STRING_LIST:
                if current_header in string_list_types.keys():
                    string_list_types[current_header] += [line]
                else:
                    string_list_types[current_header] = [line]
            if current_type == defaults.FieldType.STRING:
                string_types[current_header] = line
            if current_type == defaults.FieldType.INT:
                int_types[current_header] = int(line)

    data.close()
    merged_dict: Dict[str, Union[int, str, List[str]]] = {**int_types, **string_types, **string_list_types}
    return models.PackageDesc(**merged_dict)


def _transform_package_desc_to_output_package(
    desc: models.PackageDesc, files: Optional[models.Files]
) -> models.OutputPackage:
    """Transform a PackageDesc model and an accompanying Files model to an OutputPackage model

    Parameters
    ----------
    desc: models.PackageDesc
        A pydantic model, that has all required attributes (apart from the list of files) to create an OutputPackage
        model
    files: models.Files:
        A pydantic model, that represents the list of files, that belong to the package described by desc

    Returns
    -------
    models.OutputPackage
        A pydantic model, that describes a package and its list of files
    """

    desc_dict = desc.dict()
    # remove attributes, that are represented on the pkgbase level
    for name in ["base", "makedepends", "packager", "version"]:
        if desc_dict.get(name):
            del desc_dict[name]

    if files:
        return models.OutputPackage(**desc_dict, **files.dict())
    else:
        return models.OutputPackage(**desc_dict)
