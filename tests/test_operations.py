from pathlib import Path
from typing import Tuple

from pytest import mark

from repod import operations
from repod.repo.management.outputpackage import OutputPackageBaseV1


@mark.asyncio
async def test_db_file_as_models(files_sync_db_file: Tuple[Path, Path]) -> None:
    async for (name, model) in operations.db_file_as_models(db_path=files_sync_db_file[0]):
        assert isinstance(name, str)
        assert isinstance(model, OutputPackageBaseV1)


@mark.asyncio
async def test_dump_db_to_json_files(
    files_sync_db_file: Tuple[Path, Path],
    tmp_path: Path,
) -> None:
    await operations.dump_db_to_json_files(input_path=files_sync_db_file[0], output_path=tmp_path)


@mark.asyncio
async def test_create_db_from_json_files(outputpackagebasev1_json_files_in_dir: Path, empty_file: Path) -> None:
    await operations.create_db_from_json_files(input_path=outputpackagebasev1_json_files_in_dir, output_path=empty_file)
