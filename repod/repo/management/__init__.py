from orjson import OPT_APPEND_NEWLINE, OPT_INDENT_2, OPT_SORT_KEYS

from repod.repo.management.outputpackage import (  # noqa: F401
    Files,
    OutputBuildInfo,
    OutputPackage,
    OutputPackageBase,
    PackageDesc,
    export_schemas,
)

ORJSON_OPTION = OPT_INDENT_2 | OPT_APPEND_NEWLINE | OPT_SORT_KEYS
