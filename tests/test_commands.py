from contextlib import nullcontext as does_not_raise
from pathlib import Path
from subprocess import CalledProcessError
from typing import ContextManager, Dict, List, Optional, Union

from pytest import mark, raises

from repod import commands


@mark.parametrize("env", [(None), ({"FOO": "BAR"})])
def test__print_env(env: Optional[Dict[str, str]]) -> None:
    commands._print_env(env)


@mark.parametrize(
    "cmd, env, debug, echo, quiet, check, cwd, expectation",
    [
        (["ls", "-lah"], {"FOO": "BAR"}, False, False, False, False, None, does_not_raise()),
        (["ls", "-lah"], {"FOO": "BAR"}, True, False, False, False, None, does_not_raise()),
        (["cd", "-f"], {"FOO": "BAR"}, True, False, False, True, None, raises(CalledProcessError)),
    ],
)
@mark.asyncio
def test_run_command(
    cmd: Union[str, List[str]],
    env: Optional[Dict[str, str]],
    debug: bool,
    echo: bool,
    quiet: bool,
    check: bool,
    cwd: Union[Optional[str], Optional[Path]],
    expectation: ContextManager[str],
) -> None:
    with expectation:
        commands.run_command(cmd=cmd, env=env, debug=debug, echo=echo, quiet=quiet, check=check, cwd=cwd)
