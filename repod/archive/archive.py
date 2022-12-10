"""Functionality for package archiving."""
from __future__ import annotations

from pathlib import Path
from shutil import copy2

from pydantic import BaseModel, validator

from repod.errors import RepoManagementValidationError
from repod.repo.package.repofile import filename_parts


class CopySourceDestination(BaseModel):
    """A model describing a source and a destination path.

    Attributes
    ----------
    source: Path
        An absolute source path
    destination: Path
        An absolute destination path
    """

    source: Path
    destination: Path

    @validator("source", "destination")
    def validate_paths(cls, path: Path) -> Path:  # noqa: N805
        """Validate the source and destination paths to ensure they are absolute.

        Parameters
        ----------
        path: Path
            A path to validate

        Raises
        ------
        ValueError
            If path is not absolute

        Returns
        -------
        Path
            A validated Path
        """
        if not path.is_absolute():
            raise ValueError(f"The provided path is not absolute: {str(path)}")
        return path

    @classmethod
    def from_archive_dir(cls, source: Path, output_dir: Path) -> CopySourceDestination:
        """Create a CopySourceDestination with an archive directory as destination.

        The destination is constructed in a directory structure below output_dir, which reflects the first letter of
        source.name, the package name of source_name and source.name.

        Parameters
        ----------
        source: Path
            The source path
        output_dir: Path
            A directory below which the destination is created

        Raises
        ------
        RepoManagementValidationError
            If source is not a Path
            or if source can not be disassembled into its filename parts

        Returns
        -------
        CopySourceDestination
            An instance of CopySourceDestination
        """
        if not isinstance(source, Path):
            raise RepoManagementValidationError(f"The provided source {source} is not a Path!")
        if not isinstance(output_dir, Path):
            raise RepoManagementValidationError(f"The provided output_dir {output_dir} is not a Path!")

        try:
            parts = filename_parts(file=source)
        except ValueError as e:
            raise RepoManagementValidationError(e) from e

        return CopySourceDestination(
            source=source, destination=output_dir / parts["name"][0] / parts["name"] / source.name
        )

    def copy_file(self) -> None:
        """Copy the file from source to destination.

        The required destination directory structure is created automatically.
        """
        self.destination.parent.mkdir(mode=int("0755", base=8), parents=True, exist_ok=True)
        copy2(src=self.source, dst=self.destination)

    def remove_destination(self) -> None:
        """Remove the destination file.

        Previously created directories are left untouched.
        """
        self.destination.unlink(missing_ok=True)
