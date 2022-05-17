ABSOLUTE_DIR = r"/[A-Za-z0-9.,:;/_()@\\&$?!+%~{}<>*\-\"\'\[\]]+"
ARCHITECTURES = (
    r"(aarch64|any|arm|armv6h|armv7h|i486|i686|pentium4|riscv32|riscv64|x86_64|x86_64_v2|x86_64_v3|x86_64_v4)"
)
BUILDENVS = r"(!|)[\w\-.]+"
EMAIL = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
EPOCH = r"[1-9]+[0-9]*:"
OPTIONS = r"(!|)[\w\-.]+"
PKGREL = r"[1-9]+[0-9]*(|[.]{1}[1-9]+[0-9]*)"
PACKAGE_NAME = r"[a-z\d_@+]+[a-z\d\-._@+]*"
PACKAGER_NAME = r"[\w\s\-().]+"
SHA256 = r"^[a-f0-9]{64}$"
VERSION = r"([A-Za-z\d]+)[_+.]?[A-Za-z\d_+.]*"
