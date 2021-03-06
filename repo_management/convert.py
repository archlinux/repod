import io
from typing import Dict, List

from repo_management import defaults


def _files_data_to_dict(data: io.StringIO) -> Dict[str, List[str]]:
    """Read the contents of a 'files' file (represented as an instance of
    io.StringIO) into a dict

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
    Dict[str, List[str]]
        A dict representing the list of files
    """

    output: Dict[str, List[str]] = {defaults.FILES_JSON["%FILES%"]: []}
    line_counter = 0
    for line in data:
        line = line.strip()
        if line_counter == 0 and line not in defaults.FILES_JSON.keys():
            data.close()
            raise RuntimeError(f"The 'files' data misses its header: '{line}' was provided.")
        if line_counter > 0 and line not in defaults.FILES_JSON.keys():
            # TODO: assertions about whether the line actually represents a
            # valid path
            output[defaults.FILES_JSON["%FILES%"]] += [line]
        line_counter += 1

    data.close()
    return output
