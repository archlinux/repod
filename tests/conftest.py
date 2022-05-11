from pydantic import BaseModel

from repod.models import Files, OutputPackageBase, PackageDesc


class SchemaVersion9999(BaseModel):
    schema_version: int = 9999


class FilesV9999(Files, SchemaVersion9999):
    pass


class OutputPackageBaseV9999(OutputPackageBase, SchemaVersion9999):
    pass


class PackageDescV9999(PackageDesc, SchemaVersion9999):
    pass
