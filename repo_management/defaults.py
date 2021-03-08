from enum import IntEnum
from typing import Dict, Union


class RepoDbMemberType(IntEnum):
    UNKNOWN = 0
    DESC = 1
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
    "%LICENSE%": {"name": "licenses", "type": FieldType.STRING_LIST},
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
