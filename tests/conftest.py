import gzip
from io import BytesIO, StringIO
from os import chdir
from pathlib import Path
from random import choice
from string import digits
from tarfile import open as tarfile_open
from tempfile import NamedTemporaryFile, TemporaryDirectory
from textwrap import dedent
from typing import IO, Any, AsyncGenerator, Generator, List, Tuple

import pytest_asyncio
from pydantic import BaseModel
from pytest import fixture

from repod.common.enums import CompressionTypeEnum
from repod.convert import RepoDbFile
from repod.files import _stream_package_base_to_db, open_tarfile
from repod.files.common import ZstdTarFile
from repod.files.mtree import MTree, MTreeEntryV1
from repod.models import Files, OutputPackageBase, PackageDesc, RepoDbTypeEnum
from repod.models.package import FilesV1, OutputPackageBaseV1, OutputPackageV1


class SchemaVersion9999(BaseModel):
    schema_version: int = 9999


class FilesV9999(Files, SchemaVersion9999):
    pass


class OutputPackageBaseV9999(OutputPackageBase, SchemaVersion9999):
    pass


class PackageDescV9999(PackageDesc, SchemaVersion9999):
    pass


@fixture(scope="session")
def absolute_dir() -> str:
    return "/foo"


@fixture(
    scope="session",
    params=[
        "/",
        "foo",
        "",
    ],
)
def invalid_absolute_dir(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "aarch64",
        "any",
        "arm",
        "armv6h",
        "armv7h",
        "i486",
        "i686",
        "pentium4",
        "riscv32",
        "riscv64",
        "x86_64",
        "x86_64_v2",
        "x86_64_v3",
        "x86_64_v4",
    ],
)
def arch(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "foo",
        "!foo",
        "!1234",
        "foo123",
        "foo-123",
        "foo.123",
        "foo_",
    ],
)
def buildenv(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "",
        "!",
        "! foo",
    ],
)
def invalid_buildenv(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "foobar@mcfooface.tld",
        "foo.bar@mcfooface.tld",
        "foo.bar@mc-fooface.tld",
        "foo_bar@mc-fooface.tld",
        "foo_bar@mc.fooface.tld",
        "foo-bar@mc.fooface.tld",
        "foobar@mcfooface.tld-foo",
    ],
)
def email(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "foo",
        "@mcfooface.tld",
        "foobar@.tld",
        "foobar@mcfooface.",
        "foobar@mcfooface",
        "foobar@@mcfooface.tld",
    ],
)
def invalid_email(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "1:",
        "10:",
        "100:",
    ],
)
def epoch(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "0:",
        "1",
        ":1",
    ],
)
def invalid_epoch(request: Any) -> str:
    return str(request.param)


@fixture(scope="session")
def md5sum() -> str:
    return "".join(choice("abcdef" + digits) for x in range(32))


@fixture(
    scope="session",
    params=[
        "foo",
        "!foo",
        "!1234",
        "foo123",
        "foo-123",
        "foo.123",
        "foo_",
    ],
)
def option(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "",
        "!",
        "! foo",
    ],
)
def invalid_option(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "foo",
        "_foo",
        "@foo",
        "+foo",
        "foo_",
        "foo123",
        "foo+123",
        "foo.123",
        "foo_123",
        "foo-123",
    ],
)
def package_name(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "foo!",
        "",
        ".foo",
        "-foo",
        "fo,o",
        "fo*o",
    ],
)
def invalid_package_name(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "1",
        "10",
        "1.1",
        "1.10",
        "10.10",
    ],
)
def pkgrel(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "0",
        "1.0",
        "0.1",
        "",
    ],
)
def invalid_pkgrel(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "Foobar",
        "Foobar McFooface",
        "Foobar Mc-Fooface",
        "Foobar McFooface (The great Bar)",
        "Foobar McFooface (The great Bar..)",
        "Foobar McFooface (The 1st)",
        "foo",
    ],
)
def packager_name(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "",
        "Foobar!",
        "Foobar, McFooface",
    ],
)
def invalid_packager_name(request: Any) -> str:
    return str(request.param)


@fixture(scope="session")
def sha256sum() -> str:
    return "".join(choice("abcdef" + digits) for x in range(64))


@fixture(
    scope="session",
    params=[
        "0.0.1",
        "0_0_1",
        "0+0+1",
        "0.1.0",
        "1.0.0",
        "1.0.0.0.0.1",
        "abc1.0.0",
        "1.0.abc",
        "0",
        "1.",
        "1..",
        "foo",
    ],
)
def version(request: Any) -> str:
    return str(request.param)


@fixture(
    scope="session",
    params=[
        "-1",
        "1 0",
        "1-0",
        "1/0",
    ],
)
def invalid_version(request: Any) -> str:
    return str(request.param)


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
def tar_file(text_file: Path) -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        with NamedTemporaryFile(dir=temp_dir, suffix=".tar", delete=False) as tarfile:
            with tarfile_open(tarfile.name, mode="w:") as uncompressed_tarfile:
                uncompressed_tarfile.add(text_file.parent)
                uncompressed_tarfile.add(text_file)

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


@fixture(scope="session")
def epoch_version_pkgrel(epoch: str, version: str, pkgrel: str) -> str:
    return f"{epoch}{version}-{pkgrel}"


@fixture(scope="session")
def invalid_epoch_version_pkgrel(invalid_epoch: str, invalid_version: str, invalid_pkgrel: str) -> str:
    return f"{invalid_epoch}{invalid_version}-{invalid_pkgrel}"


@fixture(scope="module")
def buildinfov1_stringio(
    email: str,
    packager_name: str,
    sha256sum: str,
) -> Generator[StringIO, None, None]:
    buildinfov1_contents = f"""format = 1
        pkgname = foo
        pkgbase = bar
        pkgver = 1:1.0.0-1
        pkgarch = any
        pkgbuild_sha256sum = {sha256sum}
        packager = {packager_name} <{email}>
        builddate = 1
        builddir = /build
        buildenv = check
        buildenv = color
        options = debug
        options = strip
        installed = baz-1:1.0.1-1-any
        installed = beh-1:1.0.1-1-any
        """

    yield StringIO(initial_value=dedent(buildinfov1_contents).strip())


@fixture(scope="module")
def buildinfov2_stringio(
    email: str,
    packager_name: str,
    sha256sum: str,
) -> Generator[StringIO, None, None]:
    buildinfov1_contents = f"""format = 2
        pkgname = foo
        pkgbase = bar
        pkgver = 1:1.0.0-1
        pkgarch = any
        pkgbuild_sha256sum = {sha256sum}
        packager = {packager_name} <{email}>
        builddate = 1
        builddir = /build
        startdir = /startdir
        buildtool = buildtool
        buildtoolver = 1:1.0.1-1-any
        buildenv = check
        buildenv = color
        options = debug
        options = strip
        installed = baz-1:1.0.1-1-any
        installed = beh-1:1.0.1-1-any
        """

    yield StringIO(initial_value=dedent(buildinfov1_contents).strip())


@fixture(scope="function")
def valid_buildinfov1_file(buildinfov1_stringio: StringIO) -> Generator[Path, None, None]:
    with NamedTemporaryFile() as buildinfo_file:
        with open(buildinfo_file.name, mode="wt") as f:
            print(buildinfov1_stringio.getvalue(), file=f)

        yield Path(buildinfo_file.name)


@fixture(scope="function")
def valid_buildinfov2_file(buildinfov2_stringio: StringIO) -> Generator[Path, None, None]:
    with NamedTemporaryFile() as buildinfo_file:
        with open(buildinfo_file.name, mode="wt") as f:
            print(buildinfov2_stringio.getvalue(), file=f)

        yield Path(buildinfo_file.name)


@fixture(scope="session")
def outputpackagebasev1(md5sum: str, sha256sum: str) -> OutputPackageBaseV1:
    return OutputPackageBaseV1(
        base="foo",
        packager="Foobar McFooface <foobar@mcfooface.tld>",
        packages=[
            OutputPackageV1(
                arch="any",
                builddate=1,
                csize=1,
                desc="Something foo",
                filename="foo-1.0.0-1-any.pkg.tar.zst",
                files=FilesV1(files=["/foo"]),
                isize=1,
                license=["GPL3"],
                md5sum=md5sum,
                name="foo",
                pgpsig="FAKE_SIGNATURE",
                sha256sum=sha256sum,
                url="https://domain.tld",
            ),
            OutputPackageV1(
                arch="any",
                builddate=1,
                csize=1,
                desc="Something bar",
                filename="bar-1.0.0-1-any.pkg.tar.zst",
                files=FilesV1(files=["/bar"]),
                isize=1,
                license=["GPL3"],
                md5sum=md5sum,
                name="bar",
                pgpsig="FAKE_SIGNATURE",
                sha256sum=sha256sum,
                url="https://domain.tld",
            ),
        ],
        version="1.0.0-1",
    )


@pytest_asyncio.fixture(
    scope="module",
    params=[
        CompressionTypeEnum.BZIP2,
        CompressionTypeEnum.GZIP,
        CompressionTypeEnum.LZMA,
        CompressionTypeEnum.ZSTANDARD,
    ],
    ids=[
        "default bzip2",
        "default gzip",
        "default lzma",
        "default zstandard",
    ],
)
async def default_sync_db_file(
    md5sum: str,
    outputpackagebasev1: OutputPackageBaseV1,
    request: Any,
    sha256sum: str,
) -> AsyncGenerator[Tuple[Path, Path], None]:
    compression = request.param
    suffix = ""
    match compression:
        case CompressionTypeEnum.BZIP2:
            suffix = ".bz2"
        case CompressionTypeEnum.GZIP:
            suffix = ".gz"
        case CompressionTypeEnum.LZMA:
            suffix = ".xz"
        case CompressionTypeEnum.ZSTANDARD:
            suffix = ".zst"

    tar_db_name = Path(f"test.db.tar{suffix}")
    symlink_db_name = Path("test.db")

    with TemporaryDirectory() as temp_dir:
        sync_db_tarfile = Path(temp_dir) / f"test.tar{compression}"
        temp_path = Path(temp_dir)
        sync_db_tarfile = temp_path / tar_db_name
        sync_db_symlink = temp_path / symlink_db_name
        with open_tarfile(path=sync_db_tarfile, compression=compression, mode="x") as db_tarfile:
            await _stream_package_base_to_db(
                db=db_tarfile,
                model=outputpackagebasev1,
                repodbfile=RepoDbFile(),
                db_type=RepoDbTypeEnum.DEFAULT,
            )

        chdir(temp_path)
        symlink_db_name.symlink_to(sync_db_tarfile.name)
        yield (sync_db_tarfile, sync_db_symlink)


@pytest_asyncio.fixture(
    scope="module",
    params=[
        CompressionTypeEnum.BZIP2,
        CompressionTypeEnum.GZIP,
        CompressionTypeEnum.LZMA,
        CompressionTypeEnum.ZSTANDARD,
    ],
    ids=[
        "files bzip2",
        "files gzip",
        "files lzma",
        "files zstandard",
    ],
)
async def files_sync_db_file(
    md5sum: str,
    outputpackagebasev1: OutputPackageBaseV1,
    request: Any,
    sha256sum: str,
) -> AsyncGenerator[Tuple[Path, Path], None]:
    compression = request.param
    suffix = ""
    match compression:
        case CompressionTypeEnum.BZIP2:
            suffix = ".bz2"
        case CompressionTypeEnum.GZIP:
            suffix = ".gz"
        case CompressionTypeEnum.LZMA:
            suffix = ".xz"
        case CompressionTypeEnum.ZSTANDARD:
            suffix = ".zst"

    tar_db_name = Path(f"test.files.tar{suffix}")
    symlink_db_name = Path("test.files")

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        sync_db_tarfile = temp_path / tar_db_name
        sync_db_symlink = temp_path / symlink_db_name
        with open_tarfile(path=sync_db_tarfile, compression=compression, mode="x") as db_tarfile:
            await _stream_package_base_to_db(
                db=db_tarfile,
                model=outputpackagebasev1,
                repodbfile=RepoDbFile(),
                db_type=RepoDbTypeEnum.FILES,
            )

        chdir(temp_path)
        symlink_db_name.symlink_to(sync_db_tarfile.name)
        yield (sync_db_tarfile, sync_db_symlink)
