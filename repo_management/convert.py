import io
from typing import Dict, List, Optional, Union

from jinja2 import Environment, PackageLoader
from pydantic.error_wrappers import ValidationError

from repo_management import defaults, errors, models


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


def _desc_data_line_to_dicts(
    current_header: str,
    current_type: defaults.FieldType,
    line: str,
    string_list_types: Dict[str, List[str]],
    string_types: Dict[str, str],
    int_types: Dict[str, int],
) -> None:
    """Add data retrieved from a line in a 'desc' file in a repository database to respective dicts for specific types

    Parameters
    ----------
    current_header: str
        The current header under which the line is found
    current_type: str
        The type by which the header is defined by
    line: str
        The data
    string_list_types: Dict[str, List[str]]
        A dict for instances of type list string
    string_types: Dict[str, str]
        A dict for instances of type string
    int_types: Dict[str, int]
        A dict for instances of type int

    Raises
    ------
    ValueError
        If a string is provided for a field of type int, that can not be cast to type int
    """

    if current_type == defaults.FieldType.STRING_LIST:
        if current_header in string_list_types.keys():
            string_list_types[current_header] += [line]
        else:
            string_list_types[current_header] = [line]
    if current_type == defaults.FieldType.STRING:
        string_types[current_header] = line
    if current_type == defaults.FieldType.INT:
        int_types[current_header] = int(line)


def _desc_data_to_model(data: io.StringIO) -> models.PackageDesc:
    """Read the contents of a 'desc' file (represented as an instance of io.StringIO) and convert it to a pydantic model

    Parameters
    ----------
    data: io.StringIO
        A buffered I/O that represents a 'desc' file

    Raises
    ------
    errors.RepoManagementValidationError
        If a pydantic.error_wrappers.ValidationError is raised (e.g. due to a missing attribute) or if a ValueError is
        raised when converting data (e.g. when calling _desc_data_line_to_dicts())

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
            try:
                _desc_data_line_to_dicts(
                    current_header=current_header,
                    current_type=current_type,
                    line=line,
                    string_list_types=string_list_types,
                    string_types=string_types,
                    int_types=int_types,
                )
            except ValueError as e:
                raise errors.RepoManagementValidationError(
                    f"A validation error occured while creating the file:\n\n{data.getvalue()}\n{e}"
                )

    merged_dict: Dict[str, Union[int, str, List[str]]] = {**int_types, **string_types, **string_list_types}
    try:
        return models.PackageDesc(**merged_dict)
    except ValidationError as e:
        raise errors.RepoManagementValidationError(
            f"A validation error occured while creating the file:\n\n{data.getvalue()}\n{e}"
        )


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


class RepoDbFile:
    """A class for handling templates for files used in repository database files (such as 'desc' or 'files')

    Attributes
    ----------
    env: jinja2.Environment
        A jinja2 Environment, that makes the templates available

    """

    def __init__(self, enable_async: bool = False) -> None:
        """Initialize an instance of RepDbFile

        Parameters
        ----------
        enable_async: bool
            A bool indicating whether the jinja2.Environment is instantiated with enable_async (defaults to False)
        """

        self.env = Environment(
            loader=PackageLoader("repo_management", "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=enable_async,
        )

    def render_desc_template(self, model: models.PackageDesc, output: io.StringIO) -> None:
        """Use the 'desc' template to write a string to an output stream based on a model

        Parameters
        ----------
        model: models.PackageDesc
            A pydantic model with the required attributes to properly render a template for a 'desc' file
        output: io.StringIO
            An output stream to write to
        """

        template = self.env.get_template("desc.j2")
        output.write(template.render(model.dict()))

    def render_files_template(self, model: models.Files, output: io.StringIO) -> None:
        """Use the 'files' template to write a string to an output stream based on a model

        Parameters
        ----------
        model: models.Files
            A pydantic model with the required attributes to properly render a template for a 'files' file
        output: io.StringIO
            An output stream to write to
        """

        template = self.env.get_template("files.j2")
        output.write(template.render(model.dict()))
