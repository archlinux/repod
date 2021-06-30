from enum import IntEnum
from pathlib import Path
from typing import Dict, Union

DB_USER = "root"
DB_GROUP = "root"
DB_FILE_MODE = "0644"
DB_DIR_MODE = "0755"
ARCHITECTURES = ["aarch64", "arm", "armv6h", "armv7h", "i486", "i686", "pentium4", "riscv32", "riscv64", "x86_64"]
SETTINGS_LOCATION = Path("/etc/arch-repo-management/config.toml")
SETTINGS_OVERRIDE_LOCATION = Path("/etc/arch-repo-management.d/")
PACKAGE_REPO_BASE = Path("/var/lib/arch-repo-management/repo")
SOURCE_REPO_BASE = Path("/var/lib/arch-repo-management/source")

MANAGEMENT_REPO = Path("/var/lib/arch-repo-management/management/default")
PACKAGE_POOL = Path("/var/lib/arch-repo-management/pool/package/default")
SOURCE_POOL = Path("/var/lib/arch-repo-management/pool/source/default")


class RepoDbMemberType(IntEnum):
    UNKNOWN = 0
    DESC = 1
    FILES = 2


class RepoDbType(IntEnum):
    """An IntEnum to distinguish types of binary repository database files

    Attributes
    ----------
    DEFAULT: int
        Use this to identify .db files
    FILES: int
        Use this to identify .files files
    """

    DEFAULT = 0
    FILES = 2


class FieldType(IntEnum):
    STRING = 0
    INT = 1
    STRING_LIST = 2


# mapping of sections of pkgbase desc file <-> JSON key
DESC_JSON: Dict[str, Dict[str, Union[str, FieldType]]] = {
    "%BASE%": {"name": "base", "type": FieldType.STRING},
    "%VERSION%": {"name": "version", "type": FieldType.STRING},
    "%MAKEDEPENDS%": {"name": "makedepends", "type": FieldType.STRING_LIST},
    "%CHECKDEPENDS%": {"name": "checkdepends", "type": FieldType.STRING_LIST},
    "%FILENAME%": {"name": "filename", "type": FieldType.STRING},
    "%NAME%": {"name": "name", "type": FieldType.STRING},
    "%DESC%": {"name": "desc", "type": FieldType.STRING},
    "%GROUPS%": {"name": "groups", "type": FieldType.STRING_LIST},
    "%CSIZE%": {"name": "csize", "type": FieldType.INT},
    "%ISIZE%": {"name": "isize", "type": FieldType.INT},
    "%MD5SUM%": {"name": "md5sum", "type": FieldType.STRING},
    "%SHA256SUM%": {"name": "sha256sum", "type": FieldType.STRING},
    "%PGPSIG%": {"name": "pgpsig", "type": FieldType.STRING},
    "%URL%": {"name": "url", "type": FieldType.STRING},
    "%LICENSE%": {"name": "license", "type": FieldType.STRING_LIST},
    "%ARCH%": {"name": "arch", "type": FieldType.STRING},
    "%BUILDDATE%": {"name": "builddate", "type": FieldType.INT},
    "%PACKAGER%": {"name": "packager", "type": FieldType.STRING},
    "%REPLACES%": {"name": "replaces", "type": FieldType.STRING_LIST},
    "%CONFLICTS%": {"name": "conflicts", "type": FieldType.STRING_LIST},
    "%PROVIDES%": {"name": "provides", "type": FieldType.STRING_LIST},
    "%DEPENDS%": {"name": "depends", "type": FieldType.STRING_LIST},
    "%OPTDEPENDS%": {"name": "optdepends", "type": FieldType.STRING_LIST},
    "%BACKUP%": {"name": "backup", "type": FieldType.STRING_LIST},
}

FILES_JSON = {"%FILES%": {"name": "files", "type": FieldType.STRING_LIST}}
