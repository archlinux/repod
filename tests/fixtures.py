import tempfile

import orjson
import py

from repod import models


def create_empty_json_files(path: py.path.local) -> None:
    for i in range(5):
        tempfile.NamedTemporaryFile(suffix=".json", dir=path, delete=False)


def create_json_files(path: py.path.local) -> None:
    for name, files in [
        ("foo", models.package.FilesV1(files=["foo", "bar", "baz"])),
        ("bar", models.package.FilesV1(files=["foo", "bar", "baz"])),
        ("baz", None),
    ]:
        model = models.package.OutputPackageBaseV1(
            base=name,
            packager="someone",
            version="1.0.0-1",
            packages=[
                models.package.OutputPackageV1(
                    arch="foo",
                    builddate=1,
                    csize=0,
                    desc="description",
                    filename="foo.pkg.tar.zst",
                    files=files,
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
