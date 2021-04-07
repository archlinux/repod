from contextlib import nullcontext as does_not_raise
from typing import ContextManager, List, Optional, Tuple

from pytest import mark, raises

from repo_management import models


@mark.parametrize(
    "output_package, package_desc, files",
    [
        (
            models.OutputPackage(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                files=["foo", "bar"],
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
            models.PackageDesc(
                arch="foo",
                base="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                packager="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
                version="foo",
            ),
            models.Files(files=["foo", "bar"]),
        ),
        (
            models.OutputPackage(
                arch="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
            ),
            models.PackageDesc(
                arch="foo",
                base="foo",
                builddate=1,
                csize=1,
                desc="foo",
                filename="foo",
                isize=1,
                license=["foo"],
                md5sum="foo",
                name="foo",
                packager="foo",
                pgpsig="foo",
                sha256sum="foo",
                url="foo",
                version="foo",
            ),
            None,
        ),
    ],
)
def test_package_desc_get_output_package(
    output_package: models.OutputPackage,
    package_desc: models.PackageDesc,
    files: Optional[models.Files],
) -> None:
    assert output_package == package_desc.get_output_package(files)


@mark.parametrize(
    "models_list, output_package_base",
    [
        (
            [
                (
                    models.PackageDesc(
                        arch="foo",
                        base="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        packager="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                        version="foo",
                    ),
                    models.Files(files=["foo", "bar"]),
                ),
            ],
            models.OutputPackageBase(
                base="foo",
                packager="foo",
                version="foo",
                packages=[
                    models.OutputPackage(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=["foo", "bar"],
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
            ),
        ),
    ],
)
@mark.asyncio
async def test_output_package_base_get_packages_as_models(
    models_list: List[Tuple[models.PackageDesc, models.Files]],
    output_package_base: models.OutputPackageBase,
) -> None:
    assert models_list == await output_package_base.get_packages_as_models()


@mark.parametrize(
    "name, expectation",
    [
        (".foo", raises(ValueError)),
        ("-foo", raises(ValueError)),
        ("foo'", raises(ValueError)),
        ("foo", does_not_raise()),
    ],
)
def test_name(name: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert name == models.Name(name=name).name


@mark.parametrize(
    "builddate, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_builddate(builddate: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert builddate == models.BuildDate(builddate=builddate).builddate


@mark.parametrize(
    "csize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_csize(csize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert csize == models.CSize(csize=csize).csize


@mark.parametrize(
    "isize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_isize(isize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isize == models.ISize(isize=isize).isize


@mark.parametrize(
    "version, expectation",
    [
        ("1.2.3-0", raises(ValueError)),
        (".1.2.3-1", raises(ValueError)),
        ("-1.2.3-1", raises(ValueError)),
        (":1.2.3-1", raises(ValueError)),
        ("_1.2.3-1", raises(ValueError)),
        ("+1.2.3-1", raises(ValueError)),
        ("1.2.'3-1", raises(ValueError)),
        ("1.2.3-1", does_not_raise()),
        ("1:1.2.3-1", does_not_raise()),
        ("1:1.2.3r500.x.y.z.1-1", does_not_raise()),
    ],
)
def test_version_version_is_valid(version: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert version == models.Version(version=version).version


@mark.parametrize(
    "version, other_version, expectation",
    [
        ("1.2.3-1", "1.2.3-2", True),
        ("1.2.3-2", "1.2.3-1", False),
    ],
)
def test_version_is_older_than(version: str, other_version: str, expectation: bool) -> None:
    model = models.Version(version=version)
    assert model.is_older_than(other_version) is expectation


@mark.parametrize(
    "version, other_version, expectation",
    [
        ("1.2.3-1", "1.2.3-2", False),
        ("1.2.3-2", "1.2.3-1", True),
    ],
)
def test_version_is_newer_than(version: str, other_version: str, expectation: bool) -> None:
    model = models.Version(version=version)
    assert model.is_newer_than(other_version) is expectation
