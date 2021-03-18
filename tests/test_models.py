from typing import List, Optional, Tuple

from pytest import mark

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
def test_output_package_base_get_packages_as_models(
    models_list: List[Tuple[models.PackageDesc, models.Files]],
    output_package_base: models.OutputPackageBase,
) -> None:
    assert models_list == output_package_base.get_packages_as_models()
