import os
import shutil
import tarfile
import tempfile
from os.path import dirname, join, realpath
from pathlib import Path

import orjson
import py

from repo_management import models

RESOURCES = join(dirname(realpath(__file__)), "resources", "repo_db")


# TODO: rely on pytest-pacman instead of re-inventing the wheel, as soon as there is a release
def create_db_file(path: py.path.local, compression: str = "gz", remove_db: bool = False) -> Path:
    (file_number, db_file) = tempfile.mkstemp(suffix=".db", dir=path)

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = shutil.copytree(src=RESOURCES, dst=temp_dir, dirs_exist_ok=True)

        with tarfile.open(db_file, f"w:{compression}") as db_tar:
            os.chdir(repo_dir)
            for name in ["efivar-37-4", "pacman-5.2.2-1", "elfutils-0.182-1", "libelf-0.182-1"]:
                db_tar.add(name)

    if remove_db:
        os.remove(db_file)

    return Path(db_file)


def create_empty_json_files(path: py.path.local) -> None:
    for i in range(5):
        tempfile.NamedTemporaryFile(suffix=".json", dir=path, delete=False)


def create_json_files(path: py.path.local) -> None:
    for name in ["foo", "bar", "baz"]:
        model = models.OutputPackageBaseV1(
            base=name,
            packager="someone",
            version="1.0.0-1",
            packages=[
                models.OutputPackageV1(
                    arch="foo",
                    builddate=1,
                    csize=0,
                    desc="description",
                    filename="foo.pkg.tar.zst",
                    files=["foo", "bar", "baz"],
                    isize=1,
                    license=["foo"],
                    md5sum="foo",
                    name=name,
                    pgpsig="foo",
                    sha256sum="foo",
                    url="foo",
                )
            ],
        )

        output_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".json", dir=path, delete=False)
        output_file.write(
            orjson.dumps(model.dict(), option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE | orjson.OPT_SORT_KEYS)
        )
