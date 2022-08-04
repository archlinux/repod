from logging import DEBUG
from pathlib import Path
from random import sample
from re import Match, fullmatch
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture, mark

from repod.common.enums import tar_compression_types_for_filename_regex
from repod.verification import pgp


@mark.parametrize("verifies, result", [(True, True), (False, False)])
@patch("repod.verification.pgp.run_command")
def test_pacmankeyverifier_verify(
    run_command_mock: Mock, caplog: LogCaptureFixture, verifies: bool, result: bool
) -> None:
    caplog.set_level(DEBUG)
    package = Path("package")
    signature = Path("signature")
    error_message = "error_message"
    result_mock = Mock()
    result_mock.returncode = 0 if verifies else 1
    result_mock.stderr = error_message
    run_command_mock.return_value = result_mock
    print(result_mock)

    verifier = pgp.PacmanKeyVerifier()
    assert verifier.verify(package=package, signature=signature) is result


@mark.integration
@mark.xfail(reason="May fail on packages with old signatures in a system's pacman cache.")
@mark.skipif(
    not Path("/var/cache/pacman/pkg/").exists(),
    reason="Package cache in /var/cache/pacman/pkg/ does not exist",
)
def test_pacmankeyverifier_verify_with_packages(caplog: LogCaptureFixture) -> None:
    caplog.set_level(DEBUG)
    verifier = pgp.PacmanKeyVerifier()

    signatures = sorted(
        [
            path
            for path in list(Path("/var/cache/pacman/pkg/").iterdir())
            if isinstance(
                fullmatch(rf"^.*\.pkg\.tar({tar_compression_types_for_filename_regex()})\.sig$", str(path)),
                Match,
            )
        ]
    )
    if len(signatures) > 50:
        signatures = sample(signatures, 50)
    for signature in signatures:
        assert (
            verifier.verify(
                package=Path(str(signature).replace(".sig", "")),
                signature=signature,
            )
            is True
        )
