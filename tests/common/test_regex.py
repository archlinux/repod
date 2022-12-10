"""Tests for repod.common.regex."""
from re import Match, fullmatch

from pytest import mark

from repod.common import regex


@mark.regex
def test_architectures(arch: str) -> None:
    """Tests for repod.common.regex.ARCHITECTURE."""
    assert isinstance(fullmatch(regex.ARCHITECTURE, arch), Match)  # nosec: B101


@mark.regex
def test_invalid_architectures() -> None:
    """Tests for invalid repod.common.regex.ARCHITECTURE."""
    assert not isinstance(fullmatch(regex.ARCHITECTURE, "foo"), Match)  # nosec: B101


@mark.regex
def test_buildenvs(buildenv: str) -> None:
    """Tests for repod.common.regex.BUILDENVS."""
    assert isinstance(fullmatch(regex.BUILDENVS, buildenv), Match)  # nosec: B101


@mark.regex
def test_invalid_buildenvs(invalid_buildenv: str) -> None:
    """Tests for invalid repod.common.regex.BUILDENVS."""
    assert not isinstance(fullmatch(regex.BUILDENVS, invalid_buildenv), Match)  # nosec: B101


@mark.regex
def test_epoch(epoch: str) -> None:
    """Tests for repod.common.regex.EPOCH."""
    assert isinstance(fullmatch(regex.EPOCH, epoch), Match)  # nosec: B101


@mark.regex
def test_invalid_epoch(invalid_epoch: str) -> None:
    """Tests for invalid repod.common.regex.EPOCH."""
    assert not isinstance(fullmatch(regex.EPOCH, invalid_epoch), Match)  # nosec: B101


@mark.regex
def test_package_filename(
    arch: str,
    compression_type: str,
    epoch: str,
    package_name: str,
    pkgrel: str,
    version: str,
) -> None:
    """Tests for repod.common.regex.PACKAGE_FILENAME."""
    assert isinstance(  # nosec: B101
        fullmatch(regex.PACKAGE_FILENAME, f"{package_name}-{epoch}{version}-{pkgrel}-{arch}.pkg.tar{compression_type}"),
        Match,
    )


@mark.regex
def test_invalid_package_filename(
    invalid_compression_type: str,
    invalid_epoch: str,
    invalid_package_name: str,
    invalid_pkgrel: str,
    invalid_version: str,
) -> None:
    """Tests for invalid repod.common.regex.PACKAGE_FILENAME."""
    assert not isinstance(  # nosec: B101
        fullmatch(
            regex.PACKAGE_FILENAME,
            (
                f"{invalid_package_name}-{invalid_epoch}{invalid_version}{invalid_pkgrel}-"
                f"foo.pkg{invalid_compression_type}"
            ),
        ),
        Match,
    )


@mark.regex
def test_package_signature(default_filename: str, signature: str) -> None:
    """Tests for repod.common.regex.SIGNATURE_FILENAME."""
    assert isinstance(fullmatch(regex.SIGNATURE_FILENAME, f"{default_filename}{signature}"), Match)  # nosec: B101


@mark.regex
def test_invalid_package_signature(default_filename: str, invalid_signature: str) -> None:
    """Tests for repod.common.regex.SIGNATURE_FILENAME."""
    assert not isinstance(  # nosec: B101
        fullmatch(regex.SIGNATURE_FILENAME, (f"{default_filename}{invalid_signature}")),
        Match,
    )


@mark.regex
def test_md5(md5sum: str) -> None:
    """Tests for repod.common.regex.MD5."""
    assert isinstance(fullmatch(regex.MD5, md5sum), Match)  # nosec: B101
    assert not isinstance(fullmatch(regex.MD5, md5sum[0:-2]), Match)  # nosec: B101


@mark.regex
def test_options(option: str) -> None:
    """Tests for repod.common.regex.OPTIONS."""
    assert isinstance(fullmatch(regex.OPTIONS, option), Match)  # nosec: B101


@mark.regex
def test_invalid_options(invalid_option: str) -> None:
    """Tests for invalid repod.common.regex.OPTIONS."""
    assert not isinstance(fullmatch(regex.OPTIONS, invalid_option), Match)  # nosec: B101


@mark.regex
def test_package_name(package_name: str) -> None:
    """Tests for repod.common.regex.PACKAGE_NAME."""
    assert isinstance(fullmatch(regex.PACKAGE_NAME, package_name), Match)  # nosec: B101


@mark.regex
def test_invalid_package_name(invalid_package_name: str) -> None:
    """Tests for invalid repod.common.regex.PACKAGE_NAME."""
    assert not isinstance(fullmatch(regex.PACKAGE_NAME, invalid_package_name), Match)  # nosec: B101


@mark.regex
def test_packager_name(packager_name: str) -> None:
    """Tests for repod.common.regex.PACKAGER_NAME."""
    assert isinstance(fullmatch(regex.PACKAGER_NAME, packager_name), Match)  # nosec: B101


@mark.regex
def test_invalid_packager_name(invalid_packager_name: str) -> None:
    """Tests for invalid repod.common.regex.PACKAGER_NAME."""
    assert not isinstance(fullmatch(regex.PACKAGER_NAME, invalid_packager_name), Match)  # nosec: B101


@mark.regex
def test_pkgrel(pkgrel: str) -> None:
    """Tests for repod.common.regex.PKGREL."""
    assert isinstance(fullmatch(regex.PKGREL, pkgrel), Match)  # nosec: B101


@mark.regex
def test_invalid_pkgrel(invalid_pkgrel: str) -> None:
    """Tests for invalid repod.common.regex.PKGREL."""
    assert not isinstance(fullmatch(regex.PKGREL, invalid_pkgrel), Match)  # nosec: B101


@mark.regex
def test_sha256(sha256sum: str) -> None:
    """Tests for repod.common.regex.SHA256."""
    assert isinstance(fullmatch(regex.SHA256, sha256sum), Match)  # nosec: B101
    assert not isinstance(fullmatch(regex.SHA256, sha256sum[0:-2]), Match)  # nosec: B101


@mark.regex
def test_version(version: str) -> None:
    """Tests for repod.common.regex.VERSION."""
    assert isinstance(fullmatch(regex.VERSION, version), Match)  # nosec: B101


@mark.regex
def test_invalid_version(invalid_version: str) -> None:
    """Tests for invalid repod.common.regex.VERSION."""
    assert not isinstance(fullmatch(regex.VERSION, invalid_version), Match)  # nosec: B101
