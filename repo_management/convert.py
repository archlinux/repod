import io
from typing import Dict, List, Set, Union

from jinja2 import Environment, PackageLoader
from pydantic.error_wrappers import ValidationError

from repo_management import errors, models


async def _file_data_line_to_dicts(
    current_header: str,
    current_type: models.FieldTypeEnum,
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

    if current_type == models.FieldTypeEnum.STRING_LIST:
        if current_header in string_list_types.keys():
            string_list_types[current_header] += [line]
        else:
            string_list_types[current_header] = [line]
    if current_type == models.FieldTypeEnum.STRING:
        string_types[current_header] = line
    if current_type == models.FieldTypeEnum.INT:
        int_types[current_header] = int(line)


async def file_data_to_model(
    data: io.StringIO, data_type: models.RepoDbMemberTypeEnum
) -> Union[models.Files, models.PackageDescV1]:
    """Read the contents of a 'desc' or 'files' file (provided as io.StringIO) and convert it to a pydantic model

    Parameters
    ----------
    data: io.StringIO
        A buffered I/O that represents a 'desc' file
    data_type: RepoDbMemberTypeEnum
        An IntEnum specifying which type of data is converted (e.g. that of a 'desc' file or that of a 'files' file)

    Raises
    ------
    errors.RepoManagementFileError
        If an unknown file is attempted to be read
    errors.RepoManagementValidationError
        If a pydantic.error_wrappers.ValidationError is raised (e.g. due to a missing attribute) or if a ValueError is
        raised when converting data (e.g. when calling _desc_data_line_to_dicts())

    Returns
    -------
    Union[models.PackageDescV1, models.Files]
        A pydantic model, representing a 'desc' or a 'files' entry of a repository sync database
    """

    current_header = ""
    current_type: models.FieldTypeEnum
    int_types: Dict[str, int] = {}
    keys: Set[str]
    string_types: Dict[str, str] = {}
    string_list_types: Dict[str, List[str]] = {}

    match data_type:
        case models.RepoDbMemberTypeEnum.DESC:
            keys = models.get_desc_json_keys()
        case models.RepoDbMemberTypeEnum.FILES:
            keys = models.get_files_json_keys()
        case _:
            raise errors.RepoManagementFileError(
                "Unknown file type encountered while attempting to read files from a repository sync database."
            )

    for line in data:
        line = line.strip()
        if not line:
            continue

        if line in keys:
            match data_type:
                case models.RepoDbMemberTypeEnum.DESC:
                    current_header = models.get_desc_json_name(key=line)
                    current_type = models.get_desc_json_field_type(line)
                case models.RepoDbMemberTypeEnum.FILES:
                    current_header = models.get_files_json_name(key=line)
                    current_type = models.get_files_json_field_type(line)
                case _:  # pragma: no cover
                    pass
            continue

        if current_header:
            try:
                await _file_data_line_to_dicts(
                    current_header=current_header,
                    current_type=current_type,
                    line=line,
                    string_list_types=string_list_types,
                    string_types=string_types,
                    int_types=int_types,
                )
            except ValueError as e:
                raise errors.RepoManagementValidationError(
                    f"A validation error occured while reading the file:\n\n{data.getvalue()}\n{e}"
                )

    model: Union[models.PackageDescV1, models.Files]

    match data_type:
        case models.RepoDbMemberTypeEnum.DESC:
            desc_dict: Dict[str, Union[int, str, List[str]]] = {**int_types, **string_types, **string_list_types}
            try:
                model = models.PackageDescV1(**desc_dict)
            except ValidationError as e:
                raise errors.RepoManagementValidationError(
                    f"A validation error occured while reading the 'desc' file:\n\n{data.getvalue()}\n{e}"
                )
        case models.RepoDbMemberTypeEnum.FILES:
            try:
                model = models.Files(**string_list_types)
            except ValidationError as e:
                raise errors.RepoManagementValidationError(
                    f"A validation error occured while reading the 'files' file:\n\n{data.getvalue()}\n{e}"
                )
        case _:  # pragma: no cover
            pass

    return model


class RepoDbFile:
    """A class for handling templates for files used in repository database files (such as 'desc' or 'files')

    Attributes
    ----------
    env: jinja2.Environment
        A jinja2 Environment, that makes the templates available

    """

    def __init__(self, enable_async: bool = True) -> None:
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
            autoescape=True,
        )

    async def render_desc_template(self, model: models.PackageDescV1, output: io.StringIO) -> None:
        """Use the 'desc_v*' template to write a string to an output stream based on a model

        The specific desc template is chosen based upon the model's schema_version attribute.

        Parameters
        ----------
        model: models.PackageDescV1
            A pydantic model with the required attributes to properly render a template for a 'desc' file
        output: io.StringIO
            An output stream to write to
        """

        template = self.env.get_template(f"desc_v{model.schema_version}.j2")
        output.write(await template.render_async(model.dict()))

    async def render_files_template(self, model: models.Files, output: io.StringIO) -> None:
        """Use the 'files' template to write a string to an output stream based on a model

        Parameters
        ----------
        model: models.Files
            A pydantic model with the required attributes to properly render a template for a 'files' file
        output: io.StringIO
            An output stream to write to
        """

        template = self.env.get_template("files.j2")
        output.write(await template.render_async(model.dict()))
