"""Implementation of PGP based verification."""
from __future__ import annotations

from abc import ABC, abstractmethod
from logging import info
from pathlib import Path

from repod.commands import run_command


class PGPVerifier(ABC):
    """An abstract base class implementing PGP verification."""

    @abstractmethod
    def verify(self: PGPVerifier, package: Path, signature: Path) -> bool:
        """Verify a package and its accompanying signature.

        Parameters
        ----------
        package: Path
            The path to a package file
        signature: Path
            The path to a PGP signature for package

        Returns
        -------
        bool
            True if the signature can be verified, False otherwise
        """
        pass  # pragma: nocover


class PacmanKeyVerifier(PGPVerifier):
    """A class implementing PGP verification using pacman-key."""

    def verify(self: PGPVerifier, package: Path, signature: Path) -> bool:
        """Verify the detached PGP signature of a package file using pacman-key --verify.

        Parameters
        ----------
        package: Path
            The path to a package file
        signature: Path
            The path to a PGP signature for package

        Returns
        -------
        bool
            True if the signature can be verified, False otherwise
        """
        result = run_command(
            cmd=["pacman-key", "--verify", f"{signature}"],
            quiet=True,
        )

        if result.returncode != 0:
            info(f"The package file {package} could not be verified using the signature {signature}!\n{result.stderr}")
            return False

        return True
