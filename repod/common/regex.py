from repod.common.enums import (
    ArchitectureEnum,
    tar_compression_types_for_filename_regex,
)

RELATIVE_MTREE_PATH = r"[A-Za-z0-9.,:;/_()@\\&$?!+%~{}<>*\-\"\'\[\]\`^|]+"
"""
RELATIVE_MTREE_PATH may include printable ASCII characters other than space, #, =. The backslash is included as it's a
result of encoding special characters. See the mtree implementation in libarchive:
https://github.com/libarchive/libarchive/blob/v3.6.1/libarchive/archive_write_set_format_mtree.c#L307
"""
ABSOLUTE_MTREE_PATH = rf"/{RELATIVE_MTREE_PATH}"
ARCHITECTURE = rf"({ArchitectureEnum.as_or_regex()})"
B2 = r"^[a-f0-9]{128}$"
BASE64 = r"[0-9A-Za-z/+]+={0,2}"
BUILDENVS = r"(!|)[\w\-.]+"
CK = r"^[0-9]{10}$"
EPOCH = r"[1-9]+[0-9]*:"
MD5 = r"^[a-f0-9]{32}$"
OPTIONS = r"(!|)[\w\-.]+"
PKGREL = r"[1-9]+[0-9]*(|[.]{1}[1-9]+[0-9]*)"
PACKAGE_NAME = r"[a-z\d_@+]+[a-z\d\-._@+]*"
PACKAGER_NAME = r"[\w\s\-().]+"
SHA1 = r"^[a-f0-9]{40}$"
SHA224 = r"^[a-f0-9]{56}$"
SHA256 = r"^[a-f0-9]{64}$"
SHA384 = r"^[a-f0-9]{96}$"
SHA512 = r"^[a-f0-9]{128}$"
VERSION = r"([A-Za-z\d]+)[_+.]?[A-Za-z\d_+.]*"
PACKAGE_FILENAME = (
    rf"{PACKAGE_NAME}-({EPOCH}|){VERSION}-{PKGREL}-{ARCHITECTURE}"
    rf"(.pkg.tar)({tar_compression_types_for_filename_regex()})"
)
SIGNATURE_FILENAME = rf"{PACKAGE_FILENAME}(.sig)"
