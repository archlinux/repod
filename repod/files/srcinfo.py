from __future__ import annotations

from io import StringIO
from logging import debug
from pathlib import Path

from pydantic import BaseModel, HttpUrl, ValidationError, conlist, constr

from repod.common.enums import FieldTypeEnum
from repod.common.models import (
    Arch,
    Backup,
    CheckDepends,
    Conflicts,
    Depends,
    Epoch,
    Groups,
    License,
    MakeDepends,
    OptDepends,
    Options,
    PkgBase,
    PkgDesc,
    PkgName,
    PkgRel,
    PkgVer,
    Provides,
    Replaces,
    Url,
)
from repod.common.regex import (
    ARCHITECTURE,
    B2,
    CK,
    MD5,
    PGP_KEY_ID,
    SHA1,
    SHA224,
    SHA256,
    SHA384,
    SHA512,
)
from repod.errors import FileParserError
from repod.files.common import read_text_from_file

SRCINFO_ASSIGNMENTS: dict[str, tuple[str, FieldTypeEnum]] = {
    "arch": ("arch", FieldTypeEnum.STRING),
    "backup": ("backup", FieldTypeEnum.STRING_LIST),
    "b2sums": ("b2sums", FieldTypeEnum.STRING_LIST),
    "changelog": ("changelog", FieldTypeEnum.STRING),
    "checkdepends": ("checkdepends", FieldTypeEnum.STRING_LIST),
    "cksums": ("cksums", FieldTypeEnum.STRING_LIST),
    "conflicts": ("conflicts", FieldTypeEnum.STRING_LIST),
    "depends": ("depends", FieldTypeEnum.STRING_LIST),
    "epoch": ("epoch", FieldTypeEnum.INT),
    "groups": ("groups", FieldTypeEnum.STRING_LIST),
    "install": ("install", FieldTypeEnum.STRING),
    "license": ("license", FieldTypeEnum.STRING_LIST),
    "makedepends": ("makedepends", FieldTypeEnum.STRING_LIST),
    "md5sum": ("md5sums", FieldTypeEnum.STRING_LIST),
    "noextract": ("noextract", FieldTypeEnum.STRING_LIST),
    "optdepends": ("optdepends", FieldTypeEnum.STRING_LIST),
    "options": ("options", FieldTypeEnum.STRING_LIST),
    "pkgbase": ("pkgbase", FieldTypeEnum.STRING),
    "pkgdesc": ("pkgdesc", FieldTypeEnum.STRING),
    "pkgname": ("pkgname", FieldTypeEnum.STRING),
    "pkgrel": ("pkgrel", FieldTypeEnum.STRING),
    "pkgver": ("pkgver", FieldTypeEnum.STRING),
    "provides": ("provides", FieldTypeEnum.STRING_LIST),
    "replaces": ("replaces", FieldTypeEnum.STRING_LIST),
    "sha1sums": ("sha1sums", FieldTypeEnum.STRING_LIST),
    "sha224sums": ("sha224sums", FieldTypeEnum.STRING_LIST),
    "sha256sums": ("sha256sums", FieldTypeEnum.STRING_LIST),
    "sha384sums": ("sha384sums", FieldTypeEnum.STRING_LIST),
    "sha512sums": ("sha512sums", FieldTypeEnum.STRING_LIST),
    "source": ("source", FieldTypeEnum.STRING_LIST),
    "url": ("url", FieldTypeEnum.STRING),
    "validpgpkeys": ("validpgpkeys", FieldTypeEnum.STRING_LIST),
}


def parse_pairs(line: str, separator: str = " = ") -> tuple[str, str, FieldTypeEnum]:
    """Parse key-value pairs from a line of text

    The line of text represents the data contained in a .SRCINFO file.
    Keys are resolved based on SRCINFO_ASSIGMENTS.

    Parameters
    ----------
    line: str
        A line of text to be parsed
    separator: str
        A separator string by which to split the line of text

    Raises
    ------
    FileParserError
        If an invalid line of text is provided.

    Returns
    -------
    tuple[str, str, FieldTypeEnum]
        A tuple of two strings and a member of FieldTypeEnum, which represent key, value and field type extracted from
        the line of text
    """

    debug(f"Parsing: {line}")
    line = line.strip()

    try:
        extracted_key, value = [x.strip() for x in line.strip().split(separator, 1)]

        assignment_key = SRCINFO_ASSIGNMENTS.get(extracted_key)
        if assignment_key is None:
            raise FileParserError(
                f"An error occured parsing the .SRCINFO line '{line}'! "
                f"The key {extracted_key} can not be found in the type assignments for .SRCINFO keywords."
            )
        key = assignment_key[0]
        field_type = assignment_key[1]
    except ValueError as e:
        raise FileParserError(f"An error occurred while trying to parse the .SRCINFO line {line}\n{e}")

    return key, value, field_type


def pairs_to_entries(
    key: str,
    value: str,
    field_type: FieldTypeEnum,
    entries: dict[str, int | str | list[str]],
) -> None:
    """Append key value-pairs to a dict

    Values are cast based on their provided field types.
    Nested values for xdata are understood and are initialized as their target types (e.g. PkgType).

    Parameters
    ----------
    key: str
        The resolved key
    value: str
        The extracted value
    field_type: FieldTypeEnum
        A member of FieldTypeEnum based upon which value is cast to a specific type
    entries: dict[str, Any]
        The dict to which the key-value pairs are added

    Raises
    ------
    RuntimeError
        If an invalid key/ field type combination is encountered
    """

    debug(f"Attempting to add key {key} and value {value} of field type {field_type.value} to a dict...")
    match field_type:
        case FieldTypeEnum.INT if entries.get(key):
            raise FileParserError(
                "Failed parsing .SRCINFO data: "
                f"The key-value pair '{key}' => '{entries.get(key)}' exists already, unable to use value '{value}'!"
            )
        case FieldTypeEnum.INT:
            try:
                entries[key] = int(value)
            except ValueError:
                raise FileParserError(
                    "Failed parsing .SRCINFO data: " f"The value '{value}' of key {key} can not be converted to int!"
                )
        case FieldTypeEnum.STRING if entries.get(key):
            raise FileParserError(
                "Failed parsing .SRCINFO data: "
                f"The key-value pair '{key}' => '{entries.get(key)}' exists already, unable to use value '{value}'!"
            )
        case FieldTypeEnum.STRING:
            entries[key] = str(value)
        case FieldTypeEnum.STRING_LIST:
            entry = entries.get(key)
            if entry is not None and isinstance(entry, list):
                entry.append(str(value))
            else:
                entries[key] = [str(value)]
        case _:
            raise FileParserError(
                "An invalid field type has been encountered while attempting to read a .SRCINFO file."
            )


class B2Sums(BaseModel):
    """The representation of an optional list of blake2 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    b2sums: list[str] | None
        An optional list of blake2 checksum or 'SKIP' strings
    """

    b2sums: list[constr(regex=f"^({B2}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class CkSums(BaseModel):
    """The representation of an optional list of CRC-32 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    cksums: list[str] | None
        An optional list of CRC-32 checksum or 'SKIP' strings
    """

    cksums: list[constr(regex=f"^({CK}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Changelog(BaseModel):
    """The representation of an optional changelog file string in a .SRCINFO file

    Attributes
    ----------
    changelog: str | None
        An optional changelog file string
    """

    changelog: str | None


class Install(BaseModel):
    """The representation of an optional install file string in a .SRCINFO file

    Attributes
    ----------
    install: str | None
        An optional .install file string
    """

    install: str | None


class Md5Sums(BaseModel):
    """The representation of an optional list of MD5 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    md5sums: list[str] | None
        An optional list of MD5 checksum or 'SKIP' strings
    """

    md5sums: list[constr(regex=f"^({MD5}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Noextract(BaseModel):
    """The representation of an optional list of file strings in a .SRCINFO file marked for no extraction

    Attributes
    ----------
    noextract: list[str] | None
        An optional list of file string marked for no extraction
    """

    noextract: list[str] | None


class Sha1Sums(BaseModel):
    """The representation of an optional list of SHA-1 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    sha1sums: list[str] | None
        An optional list of SHA-1 checksum or 'SKIP' strings
    """

    sha1sums: list[constr(regex=f"^({SHA1}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Sha224Sums(BaseModel):
    """The representation of an optional list of SHA-224 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    sha224sums: list[str] | None
        An optional list of SHA-224 checksum or 'SKIP' strings
    """

    sha224sums: list[constr(regex=f"^({SHA224}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Sha256Sums(BaseModel):
    """The representation of an optional list of SHA-256 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    sha256sums: list[str] | None
        An optional list of SHA-256 checksum or 'SKIP' strings
    """

    sha256sums: list[constr(regex=f"^({SHA256}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Sha384Sums(BaseModel):
    """The representation of an optional list of SHA-384 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    sha384sums: list[str] | None
        An optional list of SHA-384 checksum or 'SKIP' strings
    """

    sha384sums: list[constr(regex=f"^({SHA384}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Sha512Sums(BaseModel):
    """The representation of an optional list of SHA-512 checksum or 'SKIP' strings in a .SRCINFO file

    Attributes
    ----------
    sha512sums: list[str] | None
        An optional list of SHA-512 checksum or 'SKIP' strings
    """

    sha512sums: list[constr(regex=f"^({SHA512}|SKIP)$")] | None  # type: ignore[valid-type]  # noqa: F722


class Source(BaseModel):
    """The representation of an optional list of source (file or remote artifact) strings in a .SRCINFO file

    Attributes
    ----------
    source: list[str] | None
        An optional list of source (file or remote artifact) strings
    """

    source: list[str] | None


class ValidPGPKeys(BaseModel):
    """The representation of an optional list of valid PGP key ID strings in a .SRCINFO file

    Attributes
    ----------
    validpgpkeys: list[str] | None
        An optional list of PGP key ID strings
    """

    validpgpkeys: list[constr(regex=PGP_KEY_ID)] | None  # type: ignore[valid-type]


class OptionalArch(BaseModel):
    """The representation of an optional architecture string in a .SRCINFO file

    Attributes
    ----------
    arch: str | None
        An optional architecture string of a package
    """

    arch: constr(regex=f"^{ARCHITECTURE}$") | None  # type: ignore[valid-type]  # noqa: F722


class OptionalLicense(BaseModel):
    """A model describing a single 'license' attribute

    Attributes
    ----------
    license: list[str] | None
        An optional list of license identifier strings, that describe the license(s) of a package
    """

    license: list[str]


class OptionalPkgDesc(BaseModel):
    """The representation of an optional package description string in a .SRCINFO file

    Attributes
    ----------
    pkgdesc: str | None
        An optional package description string
    """

    pkgdesc: str | None


class OptionalUrl(BaseModel):
    """The representation of an optional HTTP URL in a .SRCINFO file

    Attributes
    ----------
    url: HttpUrl | None
        An optional URL string representing the upstream project of a package
    """

    url: HttpUrl | None


class PkgBaseSection(BaseModel):
    """The representation of a pkgbase section in a .SRCINFO file

    Refer to specific implementations (e.g. PkgBaseSectionV1) for attributes.
    """

    pass


class PkgBaseSectionV1(
    Arch,
    B2Sums,
    Backup,
    Changelog,
    CheckDepends,
    CkSums,
    Conflicts,
    Depends,
    Epoch,
    Groups,
    Install,
    License,
    MakeDepends,
    Md5Sums,
    Noextract,
    OptDepends,
    Options,
    PkgBase,
    PkgBaseSection,
    PkgDesc,
    PkgRel,
    PkgVer,
    Provides,
    Replaces,
    Sha1Sums,
    Sha224Sums,
    Sha256Sums,
    Sha384Sums,
    Sha512Sums,
    Source,
    Url,
    ValidPGPKeys,
):
    """The representation of a pkgbase section in a .SRCINFO file (version 1)

    Attributes
    ----------
    arch: str
        A package architecture
    b2sums: list[str] | None
        An optional list of blake2 checksum or 'SKIP' strings
    backup: list[str] | None
        An optional list of relative file names to backup
    changelog: str | None
        An optional changelog file string
    checkdepends: list[str] | None
        An optional list of check dependencies
    cksums: list[str] | None
        An optional list of CRC-32 checksum or 'SKIP' strings
    conflicts: list[str] | None
        An optional list of packages conflicting with a package
    depends: list[str] | None
        An optional list of depdendency package names
    epoch: PositiveInt | None
        An optional positive integer representing the epoch of a package
    groups: list[str] | None
        An optional list of groups that a package belongs to
    install: str | None
        An optional install file string
    license: list[str]
        A list of license identifier strings, that describe the license(s) of a package
    makedepends: list[str] | None
        An optional list of package names required for building a package
    md5sums: list[str] | None
        An optional list of MD5 checksum or 'SKIP' strings
    noextract: list[str] | None
        An optional list of file string marked for no extraction
    optdepends: list[str] | None
        And optional list of optional dependencies of a package
    options: list[str] | None
        An optional list of strings representing makepkg.conf OPTIONS used during the creation of a package
    pkgbase: str
        A string representing the pkgbase of a package
    pkgdesc: str
        A string used as package description
    pkgrel: str
        A string representing the pkgrel (package release version) of a package
    pkgver: str
        A string representing the pkgver (upstream package version) of a package
    provides: list[str] | None
        An optional list of packages, that are virtually provided by a package
    replaces: list[str] | None
        An optional list of packages, that are virtually replaced by a package
    sha1sums: list[str] | None
        An optional list of SHA-1 checksum or 'SKIP' strings
    sha224sums: list[str] | None
        An optional list of SHA-224 checksum or 'SKIP' strings
    sha256sums: list[str] | None
        An optional list of SHA-256 checksum or 'SKIP' strings
    sha384sums: list[str] | None
        An optional list of SHA-384 checksum or 'SKIP' strings
    sha512sums: list[str] | None
        An optional list of SHA-512 checksum or 'SKIP' strings
    source: list[str] | None
        An optional list of source (file or remote artifact) strings
    url: str
        A URL string representing the upstream project of a package
    validpgpkeys: list[str] | None
        An optional list of PGP key ID strings
    """

    pass


class PkgNameSection(BaseModel):
    """The representation of a pkgname section in a .SRCINFO file (version 1)

    Refer to specific implementations (e.g. PkgNameSectionV1) for attributes.
    """

    pass


class PkgNameSectionV1(
    Backup,
    Changelog,
    Conflicts,
    Depends,
    Groups,
    Install,
    OptDepends,
    OptionalArch,
    OptionalPkgDesc,
    OptionalUrl,
    PkgName,
    PkgNameSection,
    Provides,
    Replaces,
):
    """The representation of a pkgname section in a .SRCINFO file (version 1)

    Attributes
    ----------
    arch: str | None
        An optional architecture string of a package
    backup: list[str] | None
        An optional list of relative file names to backup
    changelog: str | None
        An optional changelog file string
    conflicts: list[str] | None
        An optional list of packages conflicting with a package
    depends: list[str] | None
        An optional list of depdendency package names
    groups: list[str] | None
        An optional list of groups that a package belongs to
    install: str | None
        An optional .install file string
    optdepends: list[str] | None
        And optional list of optional dependencies of a package
    pkgdesc: str | None
        An optional package description string
    pkgname: str
        A string representing the pkgname of a package
    provides: list[str] | None
        An optional list of packages, that are virtually provided by a package
    replaces: list[str] | None
        An optional list of packages, that are virtually replaced by a package
    url: HttpUrl | None
        An optional URL string representing the upstream project of a package
    """

    pass


class SrcInfo(BaseModel):
    """The representation of a .SRCINFO file

    Refer to specific implementations (e.g. SrcInfoV1) for attributes.
    """

    @classmethod
    def from_file(cls, data: Path | StringIO) -> SrcInfo:
        """Factory method to create a SrcInfo from a file path or StringIO

        Parameters
        ----------
        data: Path | StringIO
            A Path or StringIO representing .SRCINFO file data

        Returns
        -------
        SrcInfo
            An instance of SrcInfo
        """

        if isinstance(data, (str, Path)):
            data = read_text_from_file(path=data)

        pkgbase: dict[str, int | str | list[str]] = {}
        pkgnames: list[dict[str, int | str | list[str]]] = []
        current_dict: dict[str, int | str | list[str]] = {}
        current_pkgname = 0
        for line in [line for line in data if line.strip() and not line.startswith("#")]:
            key, value, field_type = parse_pairs(line=line)

            match key:
                case "pkgbase":
                    if pkgbase:
                        raise FileParserError("Can not have more than one pkgbase per .SRCINFO file!")

                    current_dict = pkgbase
                case "pkgname":
                    if not pkgbase:
                        raise FileParserError("The pkgname section can not be the first section in a .SRCINFO file!")

                    pkgnames += [{}]
                    current_pkgname = len(pkgnames) - 1
                    current_dict = pkgnames[current_pkgname]
                case _:
                    if not pkgbase:
                        raise FileParserError(
                            f"The key-value pair '{key}' => '{value}' can not be the first entry in a .SRCINFO file!"
                        )

            pairs_to_entries(key=key, value=value, field_type=field_type, entries=current_dict)

        try:
            return SrcInfoV1(
                pkgbase=PkgBaseSectionV1(**pkgbase),  # pyright: ignore
                pkgnames=[PkgNameSectionV1(**pkgname) for pkgname in pkgnames],  # pyright: ignore
            )
        except ValidationError as e:
            raise FileParserError(e)


class SrcInfoV1(SrcInfo):
    """The representation of a .SRCINFO file (version 1)

    Attributes
    ----------
    pkgbase: PkgBaseSectionV1
        A PkgBaseSectionV1 describing the pkgbase section of the .SRCINFO file
    pkgnames: list[PkgNameSectionV1]
        A list of PkgNameSectionV1 (with at least one item) describing the pkgname sections of the .SRCINFO file
    """

    pkgbase: PkgBaseSectionV1
    pkgnames: conlist(PkgNameSectionV1, min_items=1)  # type: ignore[valid-type]


def export_schemas(output: Path | str) -> None:
    """Export the JSON schema of selected pydantic models to an output directory

    Parameters
    ----------
    output: Path
        A path to which to output the JSON schema files

    Raises
    ------
    RuntimeError
        If output is not an existing directory
    """

    classes = [SrcInfoV1, PkgBaseSectionV1, PkgNameSectionV1]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
