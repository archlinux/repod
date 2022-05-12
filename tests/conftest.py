import gzip
from io import BytesIO, StringIO
from pathlib import Path
from random import choice
from string import digits
from tarfile import open as tarfile_open
from tempfile import NamedTemporaryFile, TemporaryDirectory
from textwrap import dedent
from typing import IO, Any, Generator, List

from pydantic import BaseModel
from pytest import fixture

from repod.files.mtree import MTree, MTreeEntryV1
from repod.files.package import ZstdTarFile
from repod.models import Files, OutputPackageBase, PackageDesc


class SchemaVersion9999(BaseModel):
    schema_version: int = 9999


class FilesV9999(Files, SchemaVersion9999):
    pass


class OutputPackageBaseV9999(OutputPackageBase, SchemaVersion9999):
    pass


class PackageDescV9999(PackageDesc, SchemaVersion9999):
    pass


@fixture(scope="function")
def mtreeentryv1_stringio() -> Generator[StringIO, None, None]:
    mtree_contents = """
        #mtree
        /set type=file uid=0 gid=0 mode=644
        ./.BUILDINFO time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
        sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
        ./.INSTALL time=1651787473.0 size=808 md5digest=d96cc20315471e332a06c4261590b505 \
        sha256digest=96fc0c8b3aa4011de41c9dd1ba95e63bf2e9767daa801c14bea1d57359baf307
        ./.PKGINFO time=1651787473.0 size=1689 md5digest=76ff63a0094096fabe790fb35daadf79 \
        sha256digest=e15a57a4ddb0fa9feddbe410f395524b25be345d17f75f5f2ccc273034d388bc
        /set mode=755
        ./etc time=1651787473.0 type=dir
        ./etc/foo time=1651787473.0 type=dir
        ./etc/foo/foo.conf time=1651787473.0 mode=644 size=2761 md5digest=c6e1c562468738e93335f2e2ce314e8b \
        sha256digest=87d2b2075fbb24eb1108fed7ef9f2971d7954ae0894b1405425a04ff9e1df49e
        ./etc/foo.conf.d time=1651787473.0 type=dir
        ./usr time=1651787473.0 type=dir
        ./usr/share time=1651787473.0 type=dir
        ./usr/share/foo time=1651787473.0 type=dir
        ./usr/share/foo/conf time=1651787473.0 type=dir
        ./usr/share/foo/conf/override.conf time=1651787473.0 mode=777 type=link link=/etc/foo.conf.d/override.conf
        """

    yield StringIO(initial_value=mtree_contents.strip())


@fixture(
    scope="function",
    params=[
        (
            """
            #mtree
            /set type=file uid=0 gid=2000 mode=644
            ./.BUILDINFO time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                    sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=644
            ./.BUILDINFO time=1651787473.0 mode=777 type=link link=/.PKGINFÖ
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=644
            ./.BUILDINFO time=1651787473.0 size=5651 md5digest=df35b8a74755b3a93997b05793c \
                    sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=79878
            ./.BUILDINFO time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                    sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=644
            ./.BUILDINFÖ time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                    sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=644
            ./.BUILDINFO time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                    sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a6425153129
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=644
            ./.BUILDINFO time=1651787473.0 size=-1 md5digest=f712adf35b8a74755b3a93997b05793c \
                sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=file uid=0 gid=0 mode=644
            ./.BUILDINFO time=-1 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=foo uid=0 gid=0 mode=644
            ./.BUILDINFO time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
        (
            """
            #mtree
            /set type=file uid=2000 gid=0 mode=644
            ./.BUILDINFO time=1651787473.0 size=5651 md5digest=f712adf35b8a74755b3a93997b05793c \
                sha256digest=ed4e5855da200753eaf00cd584f017bef6910c09f70d72e4a642515312919804
            """
        ),
    ],
    ids=[
        "invalid_gid",
        "invalid_link",
        "invalid_md5",
        "invalid_mode",
        "invalid_name",
        "invalid_sha256",
        "invalid_size",
        "invalid_time",
        "invalid_type",
        "invalid_uid",
    ],
)
def invalid_mtreeentryv1_stringio(request: Any) -> Generator[StringIO, None, None]:
    entry = dedent(request.param).strip()
    print(entry)
    yield StringIO(initial_value=entry)


@fixture(scope="function")
def mtreeentryv1_internals() -> Generator[List[MTreeEntryV1], None, None]:
    base = {
        "gid": 0,
        "link": None,
        "md5": "".join(choice("abcdef" + digits) for x in range(32)),
        "mode": "0644",
        "sha256": "".join(choice("abcdef" + digits) for x in range(64)),
        "time": 1000,
        "type_": "file",
        "uid": 0,
    }

    yield [MTreeEntryV1(name=name, **base) for name in ["/.BUILDINFO", "/.INSTALL", "/.MTREE", "/.PKGINFO"]]


@fixture(scope="function")
def mtreeentryv1_dir() -> Generator[MTreeEntryV1, None, None]:
    yield MTreeEntryV1(
        gid=0,
        link=None,
        md5="".join(choice("abcdef" + digits) for x in range(32)),
        mode="0755",
        name="/foo/dir",
        sha256="".join(choice("abcdef" + digits) for x in range(64)),
        time=1000,
        type_="dir",
        uid=0,
    )


@fixture(scope="function")
def mtreeentryv1_file() -> Generator[MTreeEntryV1, None, None]:
    yield MTreeEntryV1(
        gid=0,
        link=None,
        md5="".join(choice("abcdef" + digits) for x in range(32)),
        mode="0644",
        name="/foo/file",
        sha256="".join(choice("abcdef" + digits) for x in range(64)),
        time=1000,
        type_="file",
        uid=0,
    )


@fixture(scope="function")
def mtreeentryv1_link() -> Generator[MTreeEntryV1, None, None]:
    yield MTreeEntryV1(
        gid=0,
        link="/foo/target",
        md5="".join(choice("abcdef" + digits) for x in range(32)),
        mode="0777",
        name="/foo/link",
        sha256="".join(choice("abcdef" + digits) for x in range(64)),
        time=1000,
        type_="link",
        uid=0,
    )


@fixture(scope="function")
def valid_mtree(
    mtreeentryv1_dir: MTreeEntryV1,
    mtreeentryv1_file: MTreeEntryV1,
    mtreeentryv1_link: MTreeEntryV1,
    mtreeentryv1_internals: List[MTreeEntryV1],
) -> Generator[MTree, None, None]:
    yield MTree(
        entries=[
            mtreeentryv1_dir,
            mtreeentryv1_file,
            mtreeentryv1_link,
        ]
        + mtreeentryv1_internals,
    )


@fixture(scope="function")
def valid_mtree_file(mtreeentryv1_stringio: StringIO) -> Generator[Path, None, None]:
    with NamedTemporaryFile() as mtree_file:
        with gzip.open(filename=mtree_file.name, mode="wt") as gzip_mtree:
            gzip_mtree.write(mtreeentryv1_stringio.getvalue())

        yield Path(mtree_file.name)


@fixture(scope="function")
def valid_mtree_bytesio(valid_mtree_file: Path) -> Generator[IO[bytes], None, None]:
    with open(valid_mtree_file, mode="rb") as gzip_mtree:
        yield BytesIO(gzip_mtree.read())


@fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@fixture(scope="function")
def text_file(temp_dir: Path) -> Generator[Path, None, None]:
    with NamedTemporaryFile(dir=temp_dir, suffix=".txt", delete=False) as temp_file:
        with open(temp_file.name, "w") as f:
            print("foo", file=f)

        yield Path(temp_file.name)


@fixture(scope="function")
def bz2_file(text_file: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        with NamedTemporaryFile(dir=temp_dir, suffix=".bz2", delete=False) as tarfile:
            with tarfile_open(tarfile.name, mode="w:bz2") as compressed_tarfile:
                compressed_tarfile.add(text_file.parent)
                compressed_tarfile.add(text_file)

        yield Path(tarfile.name)


@fixture(scope="function")
def gz_file(text_file: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        with NamedTemporaryFile(dir=temp_dir, suffix=".gz", delete=False) as tarfile:
            with tarfile_open(tarfile.name, mode="w:gz") as compressed_tarfile:
                compressed_tarfile.add(text_file.parent)
                compressed_tarfile.add(text_file)

        yield Path(tarfile.name)


@fixture(scope="function")
def xz_file(text_file: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        with NamedTemporaryFile(dir=temp_dir, suffix=".xz", delete=False) as tarfile:
            with tarfile_open(tarfile.name, mode="w:xz") as compressed_tarfile:
                compressed_tarfile.add(text_file.parent)
                compressed_tarfile.add(text_file)

        yield Path(tarfile.name)


@fixture(scope="function")
def zst_file(text_file: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        with NamedTemporaryFile(dir=temp_dir, suffix=".zst", delete=False) as tarfile:
            with ZstdTarFile(tarfile.name, mode="w") as compressed_tarfile:
                compressed_tarfile.add(text_file.parent)
                compressed_tarfile.add(text_file)

        yield Path(tarfile.name)
