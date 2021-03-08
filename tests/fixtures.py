import os
import shutil
import tarfile
import tempfile
from os.path import dirname, join, realpath
from pathlib import Path

RESOURCES = join(dirname(realpath(__file__)), "resources", "repo_db")


# TODO: rely on pytest-pacman instead of re-inventing the wheel, as soon as there is a release
def create_db_file(compression: str = "gz", remove_db: bool = False) -> Path:
    (file_number, db_file) = tempfile.mkstemp(suffix=".db")
    temp_dir = tempfile.mkdtemp()
    repo_dir = shutil.copytree(src=RESOURCES, dst=temp_dir, dirs_exist_ok=True)

    with tarfile.open(db_file, f"w:{compression}") as db_tar:
        os.chdir(repo_dir)
        for name in ["efivar-37-4", "pacman-5.2.2-1", "elfutils-0.182-1", "libelf-0.182-1"]:
            db_tar.add(name)

    shutil.rmtree(temp_dir)
    if remove_db:
        os.remove(db_file)

    return Path(db_file)
