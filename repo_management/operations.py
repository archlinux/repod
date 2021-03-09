from os.path import join
from pathlib import Path
from typing import Dict, Iterator, Tuple

import orjson

from repo_management import convert, defaults, files, models


def db_file_as_models(db_path: Path, compression: str = "gz") -> Iterator[Tuple[str, models.OutputPackageBase]]:
    """Read a repository database and yield the name of each pkgbase and the respective data (represented as an instance
    of models.OutputPackageBase) in a Tuple.

    Parameters
    ----------
    db_path: Path
        A Path representing a repository database file
    compression: str
        The compression used for the repository database file (support depends on tarfile). Defaults to "gz" (gzip
        compression)

    Returns
    -------
    Iterator[Tuple[str, models.OutputPackageBase]]:
        A Tuple holding the name of a pkgbase and its accompanying data in an instance of models.OutputPackageBase
    """

    packages: Dict[str, models.OutputPackageBase] = {}
    package_descs: Dict[str, models.PackageDesc] = {}
    package_files: Dict[str, models.Files] = {}
    for member in files._db_file_member_as_model(db_file=files._read_db_file(db_path=db_path, compression=compression)):
        if member.member_type == defaults.RepoDbMemberType.DESC:
            package_descs.update({member.name: convert._desc_data_to_model(member.data)})
        if member.member_type == defaults.RepoDbMemberType.FILES:
            package_files.update({member.name: convert._files_data_to_model(member.data)})

    for (name, package_desc) in package_descs.items():
        if packages.get(package_desc.base):
            packages[package_desc.base].packages += [
                convert._transform_package_desc_to_output_package(desc=package_desc, files=package_files.get(name))
            ]
        else:
            packages.update(
                {
                    package_desc.base: models.OutputPackageBase(
                        makedepends=package_desc.makedepends,
                        packager=package_desc.packager,
                        version=package_desc.version,
                        packages=[
                            convert._transform_package_desc_to_output_package(
                                desc=package_desc, files=package_files.get(name)
                            )
                        ],
                    )
                }
            )

    for (name, package) in packages.items():
        yield (name, package)


def dump_db_to_json_files(input_path: Path, output_path: Path) -> None:
    """Read a repository database file and dump each pkgbase contained in it to a separate JSON file below a defined
    output directory

    Parameters
    ----------
    input_path: Path
        The input file to read and parse
    output_path: Path
        A directory in which to
    """

    for name, model in db_file_as_models(db_path=input_path):
        with open(join(output_path, f"{name}.json"), "wb") as output_file:
            output_file.write(
                orjson.dumps(
                    model.dict(), option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE | orjson.OPT_SORT_KEYS
                )
            )
