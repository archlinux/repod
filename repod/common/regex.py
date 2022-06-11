from repod.common.defaults import architectures_for_architecture_regex
from repod.common.enums import (
    pkg_types_for_pkgtype_regex,
    tar_compression_types_for_filename_regex,
)

RELATIVE_MTREE_PATH = r"[A-Za-z0-9.,:;/_()@\\&$?!+%~{}<>*\-\"\'\[\]]+"
ABSOLUTE_MTREE_PATH = rf"/{RELATIVE_MTREE_PATH}"
ARCHITECTURE = rf"({architectures_for_architecture_regex()})"
BASE64 = r"[0-9A-Za-z/+]+={0,2}"
BUILDENVS = r"(!|)[\w\-.]+"
EPOCH = r"[1-9]+[0-9]*:"
MD5 = r"^[a-f0-9]{32}$"
OPTIONS = r"(!|)[\w\-.]+"
PKGREL = r"[1-9]+[0-9]*(|[.]{1}[1-9]+[0-9]*)"
PACKAGE_NAME = r"[a-z\d_@+]+[a-z\d\-._@+]*"
PACKAGER_NAME = r"[\w\s\-().]+"
PKGTYPE = rf"{pkg_types_for_pkgtype_regex()}"
RELATIVE_PATH = r"[^/][\w\d\s.,:;/_=#()@\\&$?!+%~{}<>*\-\"\'\[\]\`^]+"
ABSOLUTE_PATH = rf"/{RELATIVE_PATH}"
SHA256 = r"^[a-f0-9]{64}$"
VERSION = r"([A-Za-z\d]+)[_+.]?[A-Za-z\d_+.]*"
FILENAME = (
    rf"{PACKAGE_NAME}-({EPOCH}|){VERSION}-{PKGREL}-{ARCHITECTURE}"
    rf"(.pkg.tar)({tar_compression_types_for_filename_regex()})"
)
