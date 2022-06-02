import io
from typing import Dict, List, Set, Union

from jinja2 import Environment, PackageLoader, TemplateNotFound

from repod import errors, models
from repod.common.enums import FieldTypeEnum


async def file_data_to_model(
    data: io.StringIO, data_type: models.RepoDbMemberTypeEnum, name: str
) -> Union[models.Files, models.PackageDesc]:
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
    Union[models.PackageDesc, models.Files]
        A pydantic model, representing a 'desc' or a 'files' entry of a repository sync database
    """

    current_header = ""
    current_type: FieldTypeEnum
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
                f"Unknown file type encountered while attempting to read data for package '{name}' "
                "from a repository sync database."
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

    model: Union[models.PackageDesc, models.Files]

    match data_type:
        case models.RepoDbMemberTypeEnum.DESC:
            desc_dict: Dict[str, Union[int, str, List[str]]] = {**int_types, **string_types, **string_list_types}
            try:
                model = models.PackageDesc.from_dict(desc_dict)
            except errors.RepoManagementValidationError as e:
                raise errors.RepoManagementValidationError(
                    f"An error occured while validating the 'desc' file of package '{name}':\n"
                    f"\n{data.getvalue()}\n{e}"
                )
        case models.RepoDbMemberTypeEnum.FILES:
            try:
                model = models.Files.from_dict(data=string_list_types)
            except errors.RepoManagementValidationError as e:
                raise errors.RepoManagementValidationError(
                    f"An error occured while validating the 'files' file of package '{name}':\n"
                    f"\n{data.getvalue()}\n{e}"
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
            loader=PackageLoader("repod", "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=enable_async,
        )

    async def render_desc_template(self, model: models.PackageDesc, output: io.StringIO) -> None:
        """Use the 'desc_v*' template to write a string to an output stream based on a model

        The specific desc template is chosen based upon the model's schema_version attribute.

        Parameters
        ----------
        model: models.PackageDesc
            A pydantic model with the required attributes to properly render a template for a 'desc' file
        output: io.StringIO
            An output stream to write to

        Raises
        ------

        """

        template_file = f"desc_v{model.get_schema_version()}.j2"
        try:
            template = self.env.get_template(template_file)
        except TemplateNotFound:
            raise errors.RepoManagementFileNotFoundError(
                f"The 'desc' template file {template_file} could not be found!"
            )
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

        template_file = f"files_v{model.get_schema_version()}.j2"
        try:
            template = self.env.get_template(template_file)
        except TemplateNotFound:
            raise errors.RepoManagementFileNotFoundError(
                f"The 'desc' template file {template_file} could not be found!"
            )
        output.write(await template.render_async(model.dict()))
