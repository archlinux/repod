"""Utility functions for running external commands."""
from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError  # nosec: B404

from subprocess_tee import CompletedProcess, run  # nosec: B404


def _print_env(env: dict[str, str] | None) -> None:
    """Print the environment variables from a dict.

    Parameters
    ----------
    env: dict[str, str] | None
        An optional dict with environment variables and their values
    """
    if env:
        for (key, value) in sorted(env.items()):
            print(f"{key}: {value}")


def run_command(
    cmd: str | list[str],
    env: dict[str, str] | None = None,
    debug: bool = False,
    echo: bool = False,
    quiet: bool = False,
    check: bool = False,
    cwd: str | Path | None = None,
) -> CompletedProcess:
    """Run a command.

    Parameters
    ----------
    cmd: str | list[str]
        A string or list of strings that will be passed to subprocess.run()
    env: dict[str, str] | None
        A dict of environment variables and their respective values (defaults to None)
    debug: bool
        Whether to run in debug mode, which prints environment variables and command output (defaults to False)
    echo: bool
        Whether to print the command before running it (defaults to False)
    quiet: bool
        Whether to print the output of command while running it (defaults to False)
    check: bool
        Whether to check the return code of the command, which implies raising CallecProcessError (defaults to False)
    cwd: str | Path | None
        In which directory to run the command (defaults to None, which means current working directory)

    Raises
    ------
    CalledProcessError
        If check is True and the commands return code is not 0

    Returns
    -------
    CompletedProcess
        The result of the command
    """
    if debug:
        _print_env(env)

    result = run(
        cmd,
        env=env,
        stdout=PIPE,
        stderr=STDOUT,
        echo=echo or debug,
        quiet=quiet,
        cwd=cwd,
    )
    if result.returncode != 0 and check:
        raise CalledProcessError(
            returncode=result.returncode,
            cmd=result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result
