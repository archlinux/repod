import io
from contextlib import nullcontext as does_not_raise
from os.path import dirname, join, realpath
from typing import ContextManager

from pytest import mark, raises

from repo_management import convert

RESOURCES = join(dirname(realpath(__file__)), "resources")


@mark.parametrize(
    "file_data, expectation",
    [
        ("%FILES%\nusr/\nusr/lib/\n", does_not_raise()),
        ("%FILES%usr/\nusr/lib/\n", raises(RuntimeError)),
        ("usr/\nusr/lib/\n", raises(RuntimeError)),
        ("usr/%FILES%\nusr/lib/\n", raises(RuntimeError)),
    ],
)
def test__files_data_to_dict(
    file_data: str,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        convert._files_data_to_dict(data=io.StringIO(file_data))
