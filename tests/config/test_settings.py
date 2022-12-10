from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import DEBUG, debug
from pathlib import Path
from typing import ContextManager
from unittest.mock import Mock, call, patch

from pydantic import AnyUrl
from pytest import LogCaptureFixture, mark, raises

from repod.common.enums import (
    ArchitectureEnum,
    CompressionTypeEnum,
    RepoDirTypeEnum,
    RepoTypeEnum,
    SettingsTypeEnum,
)
from repod.config import settings


def test_architecture_validate_architecture(default_arch: str) -> None:
    assert settings.Architecture(architecture=default_arch)  # nosec: B101

    with raises(ValueError):
        settings.Architecture(architecture="foo")


@mark.parametrize(
    "url, expectation",
    [
        (None, does_not_raise()),
        ("https://foo.bar", does_not_raise()),
        ("ssh://git@foo.bar", does_not_raise()),
        ("ssh://foo.bar", raises(ValueError)),
        ("http://foo.bar", raises(ValueError)),
    ],
)
def test_mangement_repo(
    url: str,
    expectation: ContextManager[str],
    empty_dir: Path,
) -> None:
    with expectation:
        assert settings.ManagementRepo(  # nosec: B101
            directory=empty_dir,
            url=url,
        )


@mark.parametrize(
    "name, debug_repo, staging_repo, staging_debug_repo, testing_repo, testing_debug_repo, expectation",
    [
        (Path("foo"), None, None, None, None, None, does_not_raise()),
        (Path("foo"), None, Path("stage"), None, None, None, does_not_raise()),
        (Path("foo"), None, None, None, Path("test"), None, does_not_raise()),
        (Path("foo"), Path("dbg"), None, None, None, None, does_not_raise()),
        (Path("foo"), Path("dbg"), None, None, Path("test"), Path("test-dbg"), does_not_raise()),
        (Path("foo"), Path("dbg"), Path("stage"), Path("stage-dbg"), None, None, does_not_raise()),
        (Path("foo"), Path("dbg"), Path("stage"), Path("stage-dbg"), Path("test"), Path("test-dbg"), does_not_raise()),
        (Path("foo"), Path("dbg"), Path("stage"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("test"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("stage"), Path("stage-dbg"), Path("test"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("stage"), None, Path("test"), Path("test-dbg"), raises(ValueError)),
        (Path("foo"), Path("dbg"), None, Path("stage-debug"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, None, Path("test-dbg"), raises(ValueError)),
        (Path("foo"), None, Path("stage"), Path("stage-debug"), None, None, raises(ValueError)),
        (Path("foo"), None, None, None, Path("test"), Path("test-dbg"), raises(ValueError)),
        (Path("FOO"), None, None, None, None, None, raises(ValueError)),
        (Path(".foo"), None, None, None, None, None, raises(ValueError)),
        (Path("-foo"), None, None, None, None, None, raises(ValueError)),
        (Path("."), None, None, None, None, None, raises(ValueError)),
        (Path(" foo"), None, None, None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg "), None, None, None, None, raises(ValueError)),
        (Path("foo"), None, Path("st "), None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st-dbg "), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst "), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("tst-dbg "), raises(ValueError)),
        (Path("foo"), Path("foo"), None, None, None, None, raises(ValueError)),
        (Path("foo"), Path("foo/dbg"), None, None, None, None, raises(ValueError)),
        (Path("foo"), None, Path("foo"), None, None, None, raises(ValueError)),
        (Path("foo"), None, Path("foo/st"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("foo"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("foo/st-dbg"), None, None, raises(ValueError)),
        (Path("foo"), None, None, None, Path("foo"), None, raises(ValueError)),
        (Path("foo"), None, None, None, Path("foo/tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("foo"), raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("foo/tst-dbg"), raises(ValueError)),
        (Path("dbg/foo"), Path("dbg"), None, None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("dbg"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("dbg/st"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("dbg"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("dbg/st-dbg"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("dbg"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("dbg/tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("dbg"), raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("dbg/tst-dbg"), raises(ValueError)),
        (Path("st/foo"), None, Path("st"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("st"), Path("st"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("st/dbg"), Path("st"), None, None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st/st-dbg"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st"), None, None, raises(ValueError)),
        (Path("foo"), None, Path("st"), None, Path("st"), None, raises(ValueError)),
        (Path("foo"), None, Path("st"), None, Path("st/tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), None, Path("tst"), Path("st"), raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), None, Path("tst"), Path("st/tst-dbg"), raises(ValueError)),
        (Path("st-dbg/foo"), Path("dbg"), Path("st"), Path("st-dbg"), None, None, raises(ValueError)),
        (Path("foo"), Path("st-dbg/dbg"), Path("st"), Path("st-dbg"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st-dbg"), Path("st-dbg"), None, None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st-dbg"), Path("st-dbg"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st-dbg"), Path("st-dbg/tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st-dbg"), Path("tst"), Path("st-dbg"), raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("st-dbg"), Path("tst"), Path("st-dbg/tst-dbg"), raises(ValueError)),
        (Path("tst/foo"), None, None, None, Path("tst"), None, raises(ValueError)),
        (Path("foo"), Path("tst/dbg"), None, None, Path("tst"), None, raises(ValueError)),
        (Path("foo"), None, Path("tst"), None, Path("tst"), None, raises(ValueError)),
        (Path("foo"), None, Path("tst/st"), None, Path("tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("tst"), Path("tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("tst/stg-dbg"), Path("tst"), None, raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("tst"), raises(ValueError)),
        (Path("foo"), Path("dbg"), None, None, Path("tst"), Path("tst/tst-dbg"), raises(ValueError)),
        (Path("tst-dbg/foo"), Path("dbg"), None, None, Path("tst"), Path("tst-dbg"), raises(ValueError)),
        (Path("foo"), Path("tst-dbg/dbg"), None, None, Path("tst"), Path("tst-dbg"), raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("tst-dbg"), None, Path("tst"), Path("tst-dbg"), raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("tst-dbg/st"), None, Path("tst"), Path("tst-dbg"), raises(ValueError)),
        (Path("foo"), Path("dbg"), Path("st"), Path("tst-dbg"), Path("tst"), Path("tst-dbg"), raises(ValueError)),
        (
            Path("foo"),
            Path("dbg"),
            Path("st"),
            Path("tst-dbg/st-dbg"),
            Path("tst"),
            Path("tst-dbg"),
            raises(ValueError),
        ),
    ],
)
def test_package_repo(
    name: Path,
    debug_repo: Path | None,
    staging_repo: Path | None,
    staging_debug_repo: Path | None,
    testing_repo: Path | None,
    testing_debug_repo: Path | None,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    with expectation:
        assert settings.PackageRepo(  # nosec: B101
            name=name,
            debug=debug_repo,
            staging=staging_repo,
            staging_debug=staging_debug_repo,
            testing=testing_repo,
            testing_debug=testing_debug_repo,
            package_pool=None,
            source_pool=None,
            management_repo=None,
        )


@mark.parametrize(
    "debug, staging, testing",
    [
        (True, True, True),
        (False, True, True),
        (False, False, True),
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (False, True, False),
    ],
)
def test_package_repo_get_all_management_repo_dirs(
    debug: bool,
    staging: bool,
    testing: bool,
    packagerepo_in_tmp_path: settings.PackageRepo,
) -> None:

    if not debug:
        packagerepo_in_tmp_path.debug = None
    if not staging:
        packagerepo_in_tmp_path.staging = None
    if not testing:
        packagerepo_in_tmp_path.testing = None

    packagerepo_in_tmp_path.get_all_management_repo_dirs()


@mark.parametrize(
    "debug, staging, testing",
    [
        (True, True, True),
        (False, True, True),
        (False, False, True),
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (False, True, False),
    ],
)
def test_package_repo_get_all_package_repo_dirs(
    debug: bool,
    staging: bool,
    testing: bool,
    packagerepo_in_tmp_path: settings.PackageRepo,
) -> None:

    if not debug:
        packagerepo_in_tmp_path.debug = None
    if not staging:
        packagerepo_in_tmp_path.staging = None
    if not testing:
        packagerepo_in_tmp_path.testing = None

    packagerepo_in_tmp_path.get_all_package_repo_dirs()


@mark.parametrize(
    "override_location_exists, custom_config_provided",
    [
        (True, False),
        (False, False),
        (True, True),
        (False, True),
    ],
)
@patch("tomli.load", return_value={})
def test_read_toml_configuration_settings_user(
    toml_load_mock: Mock,
    empty_toml_file: Path,
    empty_toml_files_in_dir: Path,
    tmp_path: Path,
    override_location_exists: bool,
    custom_config_provided: bool,
) -> None:
    if override_location_exists:
        override_dir = empty_toml_files_in_dir
    else:
        override_dir = tmp_path / "foo"

    with patch("repod.config.settings.CUSTOM_CONFIG", empty_toml_file if custom_config_provided else None):
        with patch("repod.config.settings.SETTINGS_LOCATION", {SettingsTypeEnum.USER: empty_toml_file}):
            settings.read_toml_configuration_settings(Mock(spec=settings.UserSettings))
            with patch(
                "repod.config.settings.SETTINGS_OVERRIDE_LOCATION",
                {SettingsTypeEnum.USER: override_dir},
            ):
                settings.read_toml_configuration_settings(Mock(spec=settings.UserSettings))
                toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))

        with patch("repod.config.settings.SETTINGS_LOCATION", {SettingsTypeEnum.USER: tmp_path / "foo.toml"}):
            settings.read_toml_configuration_settings(Mock(spec=settings.UserSettings))
            with patch(
                "repod.config.settings.SETTINGS_OVERRIDE_LOCATION",
                {SettingsTypeEnum.USER: override_dir},
            ):
                settings.read_toml_configuration_settings(Mock(spec=settings.UserSettings))
                toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))


@mark.parametrize(
    "override_location_exists, custom_config_provided",
    [
        (True, False),
        (False, False),
        (True, True),
        (False, True),
    ],
)
@patch("tomli.load", return_value={})
def test_read_toml_configuration_settings_system(
    toml_load_mock: Mock,
    empty_toml_file: Path,
    empty_toml_files_in_dir: Path,
    tmp_path: Path,
    override_location_exists: bool,
    custom_config_provided: bool,
) -> None:
    if override_location_exists:
        override_dir = empty_toml_files_in_dir
    else:
        override_dir = tmp_path / "foo"

    with patch("repod.config.settings.SETTINGS_LOCATION", {SettingsTypeEnum.SYSTEM: empty_toml_file}):
        settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
        with patch(
            "repod.config.settings.SETTINGS_OVERRIDE_LOCATION",
            {SettingsTypeEnum.SYSTEM: override_dir},
        ):
            settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
            toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))

    with patch("repod.config.settings.SETTINGS_LOCATION", {SettingsTypeEnum.SYSTEM: tmp_path / "foo.toml"}):
        settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
        with patch(
            "repod.config.settings.SETTINGS_OVERRIDE_LOCATION",
            {SettingsTypeEnum.SYSTEM: override_dir},
        ):
            settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
            toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))


@mark.parametrize(
    "archiving, has_managementrepo, has_repositories",
    [
        (True, True, True),
        (True, False, False),
        (False, True, True),
        (False, False, False),
        (None, True, True),
        (None, False, False),
    ],
)
@patch("repod.config.settings.Settings.consolidate_repositories_with_defaults")
@patch("repod.config.settings.Settings.check_repository_groups_dirs")
@patch("repod.config.settings.Settings.ensure_non_overlapping_repositories")
@patch("repod.config.settings.Settings.create_repository_directories")
@patch("repod.config.settings.get_default_managementrepo")
@patch("repod.config.settings.get_default_packagerepo")
def test_systemsettings(
    get_default_packagerepo_mock: Mock,
    get_default_managementrepo_mock: Mock,
    create_repository_directories_mock: Mock,
    ensure_non_overlapping_repositories_mock: Mock,
    check_repository_groups_dirs_mock: Mock,
    consolidate_repositories_with_defaults_mock: Mock,
    archiving: bool | None,
    has_managementrepo: bool,
    has_repositories: bool,
    caplog: LogCaptureFixture,
    empty_file: Path,
) -> None:
    caplog.set_level(DEBUG)

    get_default_managementrepo_mock.return_value = settings.ManagementRepo(directory=Path("/default_management_repo"))
    get_default_packagerepo_mock.return_value = settings.PackageRepo(
        architecture="any",
        name="default",
        management_repo=settings.ManagementRepo(directory=Path("/default_management_repo")),
        package_pool=Path("/default_package_pool"),
        source_pool=Path("/default_source_pool"),
    )

    with patch("repod.config.settings.SystemSettings._management_repo_base", Path("/default/management_repo_base")):
        with patch("repod.config.settings.SystemSettings._package_pool_base", Path("/default/package_pool_base")):
            with patch("repod.config.settings.SystemSettings._package_repo_base", Path("/default/package_repo_base")):
                with patch("repod.config.settings.SystemSettings._source_pool_base", Path("/default/source_pool_base")):
                    with patch(
                        "repod.config.settings.SystemSettings._source_repo_base", Path("/default/source_repo_base")
                    ):
                        with patch("repod.config.settings.CUSTOM_CONFIG", empty_file):
                            conf = settings.SystemSettings(
                                archiving=archiving,
                                management_repo=(
                                    settings.ManagementRepo(directory=Path("/custom_management_repo"))
                                    if has_managementrepo
                                    else None
                                ),
                                repositories=[
                                    settings.PackageRepo(
                                        architecture="any",
                                        name="custom",
                                        management_repo=settings.ManagementRepo(
                                            directory=Path("/custom_management_repo")
                                        ),
                                        package_pool=Path("/custom_package_pool"),
                                        source_pool=Path("/custom_source_pool"),
                                    )
                                ]
                                if has_repositories
                                else [],
                            )
                            assert isinstance(conf, settings.SystemSettings)  # nosec: B101
                            assert len(conf.repositories) > 0  # nosec: B101

                            create_repository_directories_mock.assert_called_once()
                            ensure_non_overlapping_repositories_mock.assert_called_once()
                            check_repository_groups_dirs_mock.assert_called_once()
                            consolidate_repositories_with_defaults_mock.assert_called_once()


@mark.parametrize(
    "archiving, build_requirements_exist, has_managementrepo, has_repositories",
    [
        (True, True, True, True),
        (True, True, False, False),
        (False, False, True, True),
        (False, False, False, False),
        (None, None, True, True),
        (None, None, False, False),
    ],
)
@patch("repod.config.settings.Settings.consolidate_repositories_with_defaults")
@patch("repod.config.settings.Settings.check_repository_groups_dirs")
@patch("repod.config.settings.Settings.ensure_non_overlapping_repositories")
@patch("repod.config.settings.Settings.create_repository_directories")
@patch("repod.config.settings.get_default_managementrepo")
@patch("repod.config.settings.get_default_packagerepo")
def test_usersettings(
    get_default_packagerepo_mock: Mock,
    get_default_managementrepo_mock: Mock,
    create_repository_directories_mock: Mock,
    ensure_non_overlapping_repositories_mock: Mock,
    check_repository_groups_dirs_mock: Mock,
    consolidate_repositories_with_defaults_mock: Mock,
    archiving: bool | None,
    build_requirements_exist: bool | None,
    has_managementrepo: bool,
    has_repositories: bool,
    caplog: LogCaptureFixture,
    empty_file: Path,
) -> None:
    caplog.set_level(DEBUG)

    get_default_managementrepo_mock.return_value = settings.ManagementRepo(directory=Path("/default_management_repo"))
    get_default_packagerepo_mock.return_value = settings.PackageRepo(
        architecture="any",
        name="default",
        management_repo=settings.ManagementRepo(directory=Path("/default_management_repo")),
        package_pool=Path("/default_package_pool"),
        source_pool=Path("/default_source_pool"),
    )

    with patch("repod.config.settings.UserSettings._management_repo_base", Path("/default/management_repo_base")):
        with patch("repod.config.settings.UserSettings._package_pool_base", Path("/default/package_pool_base")):
            with patch("repod.config.settings.UserSettings._package_repo_base", Path("/default/package_repo_base")):
                with patch("repod.config.settings.UserSettings._source_pool_base", Path("/default/source_pool_base")):
                    with patch(
                        "repod.config.settings.UserSettings._source_repo_base", Path("/default/source_repo_base")
                    ):
                        with patch("repod.config.settings.CUSTOM_CONFIG", empty_file):
                            conf = settings.UserSettings(
                                archiving=archiving,
                                build_requirements_exist=build_requirements_exist,
                                management_repo=(
                                    settings.ManagementRepo(directory=Path("/custom_management_repo"))
                                    if has_managementrepo
                                    else None
                                ),
                                repositories=[
                                    settings.PackageRepo(
                                        architecture="any",
                                        build_requirements_exist=None,
                                        name="custom",
                                        management_repo=settings.ManagementRepo(
                                            directory=Path("/custom_management_repo")
                                        ),
                                        package_pool=Path("/custom_package_pool"),
                                        source_pool=Path("/custom_source_pool"),
                                    )
                                ]
                                if has_repositories
                                else [],
                            )
                            assert isinstance(conf, settings.UserSettings)  # nosec: B101
                            assert len(conf.repositories) > 0  # nosec: B101

                            create_repository_directories_mock.assert_called_once()
                            ensure_non_overlapping_repositories_mock.assert_called_once()
                            check_repository_groups_dirs_mock.assert_called_once()
                            consolidate_repositories_with_defaults_mock.assert_called_once()


@mark.parametrize(
    (
        "repo_has_architecture"
        ", repo_has_database_compression"
        ", repo_has_management_repo"
        ", repo_has_package_pool"
        ", repo_has_source_pool"
        ", repo_has_debug"
        ", repo_has_staging"
        ", repo_has_staging_debug"
        ", repo_has_testing"
        ", repo_has_testing_debug"
        ", repo_build_requirements_exists"
    ),
    [
        (True, True, True, True, True, True, True, True, True, True, None),
        (True, True, True, True, True, True, True, False, True, False, None),
        (True, True, True, True, True, True, True, True, True, False, None),
        (True, True, True, True, True, True, True, False, True, True, None),
        (True, True, True, True, True, False, True, False, True, False, None),
        (True, True, True, True, True, True, False, False, True, False, None),
        (True, True, True, True, True, True, True, False, False, False, None),
        (False, False, False, False, False, False, False, False, False, False, None),
        (True, True, True, True, True, True, True, True, True, True, True),
        (True, True, True, True, True, True, True, False, True, False, True),
        (True, True, True, True, True, True, True, True, True, False, True),
        (True, True, True, True, True, True, True, False, True, True, True),
        (True, True, True, True, True, False, True, False, True, False, True),
        (True, True, True, True, True, True, False, False, True, False, True),
        (True, True, True, True, True, True, True, False, False, False, True),
        (False, False, False, False, False, False, False, False, False, False, True),
    ],
)
def test_settings_consolidate_repositories_with_defaults(  # noqa: C901
    repo_has_architecture: bool,
    repo_has_database_compression: bool,
    repo_has_management_repo: bool,
    repo_has_package_pool: bool,
    repo_has_source_pool: bool,
    repo_has_debug: bool,
    repo_has_staging: bool,
    repo_has_staging_debug: bool,
    repo_has_testing: bool,
    repo_has_testing_debug: bool,
    repo_build_requirements_exists: bool | None,
    packagerepo_in_tmp_path: settings.PackageRepo,
    tmp_path: Path,
) -> None:
    if not repo_has_architecture:
        packagerepo_in_tmp_path.architecture = None

    if not repo_has_database_compression:
        packagerepo_in_tmp_path.database_compression = None

    if not repo_has_management_repo:
        packagerepo_in_tmp_path.management_repo = None

    if not repo_has_package_pool:
        packagerepo_in_tmp_path.package_pool = None

    if not repo_has_source_pool:
        packagerepo_in_tmp_path.source_pool = None

    if not repo_has_debug:
        packagerepo_in_tmp_path.debug = None
    if not repo_has_staging:
        packagerepo_in_tmp_path.staging = None
    if not repo_has_staging_debug:
        packagerepo_in_tmp_path.staging_debug = None
    if not repo_has_testing:
        packagerepo_in_tmp_path.testing = None
    if not repo_has_testing_debug:
        packagerepo_in_tmp_path.testing_debug = None

    packagerepo_in_tmp_path.build_requirements_exist = repo_build_requirements_exists

    with patch("repod.config.settings.Settings._package_repo_base", tmp_path / "_package_repo_base"):
        with patch("repod.config.settings.Settings._source_repo_base", tmp_path / "_source_repo_base"):
            with patch("repod.config.settings.Settings._package_pool_base", tmp_path / "_package_pool_base"):
                with patch("repod.config.settings.Settings._source_pool_base", tmp_path / "_source_pool_base"):
                    with patch(
                        "repod.config.settings.Settings._management_repo_base", tmp_path / "_management_repo_base"
                    ):
                        repos = settings.Settings.consolidate_repositories_with_defaults(
                            architecture=settings.DEFAULT_ARCHITECTURE,
                            archiving=None,
                            build_requirements_exist=True,
                            database_compression=settings.DEFAULT_DATABASE_COMPRESSION,
                            management_repo=settings.ManagementRepo(directory=tmp_path / settings.DEFAULT_NAME),
                            package_pool=tmp_path / "package_pool_dir",
                            repositories=[packagerepo_in_tmp_path],
                            source_pool=tmp_path / "source_pool_dir",
                        )

    assert (  # nosec: B101
        repos[0].architecture == packagerepo_in_tmp_path.architecture
        if repo_has_architecture
        else settings.DEFAULT_ARCHITECTURE
    )

    assert (  # nosec: B101
        repos[0].database_compression == packagerepo_in_tmp_path.database_compression
        if repo_has_database_compression
        else settings.DEFAULT_DATABASE_COMPRESSION
    )

    assert (  # nosec: B101
        repos[0].management_repo == packagerepo_in_tmp_path.management_repo
        if repo_has_management_repo
        else settings.ManagementRepo(directory=tmp_path / settings.DEFAULT_NAME)
    )

    assert (  # nosec: B101
        repos[0].package_pool == packagerepo_in_tmp_path.package_pool
        if repo_has_package_pool
        else tmp_path / "package_pool_dir"
    )

    assert (  # nosec: B101
        repos[0].source_pool == packagerepo_in_tmp_path.source_pool
        if repo_has_source_pool
        else tmp_path / "source_pool_dir"
    )


@mark.parametrize(
    "same_group, same_management_parent, same_package_parent, same_pool_parent, same_source_parent, expectation",
    [
        (True, True, True, True, True, does_not_raise()),
        (False, True, True, True, True, does_not_raise()),
        (True, False, True, True, True, raises(ValueError)),
        (True, True, False, True, True, raises(ValueError)),
        (True, True, True, False, True, raises(ValueError)),
        (True, True, True, True, False, raises(ValueError)),
        (False, False, False, False, False, does_not_raise()),
    ],
)
def test_settings_check_repository_groups_dirs(
    same_group: bool,
    same_management_parent: bool,
    same_package_parent: bool,
    same_pool_parent: bool,
    same_source_parent: bool,
    expectation: ContextManager[str],
    packagerepo_in_tmp_path: settings.PackageRepo,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    repo1 = packagerepo_in_tmp_path
    repo1.name = Path("repo1")
    repo1.debug = None
    repo1.staging = None
    repo1.testing = None
    repo1.group = 1

    repo2 = deepcopy(repo1)
    repo2.name = Path("repo2")
    if not same_group:
        repo2.group = None

    if same_management_parent:
        repo2._stable_management_repo_dir = repo2._stable_management_repo_dir.parent / "repo2"
    else:
        repo2._stable_management_repo_dir = repo2._stable_management_repo_dir.parent.parent / "repo2"

    if same_package_parent:
        repo2._stable_repo_dir = (
            repo2._stable_repo_dir.parent.parent / repo2.name / repo2.architecture.value  # type: ignore[union-attr]
        )
    else:
        repo2._stable_repo_dir = (
            repo2._stable_repo_dir.parent.parent
            / repo2.name
            / repo2.name
            / repo2.architecture.value  # type: ignore[union-attr]
        )

    if same_pool_parent:
        repo2._package_pool_dir = repo2._package_pool_dir.parent / repo2.name
    else:
        repo2._package_pool_dir = repo2._package_pool_dir.parent.parent / repo2.name

    if same_source_parent:
        repo2._source_pool_dir = repo2._source_pool_dir.parent / repo2.name
    else:
        repo2._source_pool_dir = repo2._source_pool_dir.parent.parent / repo2.name

    with expectation:
        settings.Settings.check_repository_groups_dirs(repositories=[repo1, repo2])


@mark.parametrize(
    "debug_repo, staging_repo, staging_debug_repo, testing_repo, testing_debug_repo",
    [
        (True, True, True, True, True),
        (False, True, True, True, True),
        (False, False, False, True, True),
        (False, True, True, False, False),
        (True, True, True, False, False),
        (False, False, False, False, False),
    ],
)
def test_settings_create_repository_directories(  # noqa: C901
    debug_repo: bool,
    staging_repo: bool,
    staging_debug_repo: bool,
    testing_repo: bool,
    testing_debug_repo: bool,
    packagerepo_in_tmp_path: settings.PackageRepo,
) -> None:
    if not debug_repo:
        packagerepo_in_tmp_path.debug = None
    if not staging_repo:
        packagerepo_in_tmp_path.staging = None
    if not staging_debug_repo:
        packagerepo_in_tmp_path.staging_debug = None
    if not testing_repo:
        packagerepo_in_tmp_path.testing = None
    if not testing_debug_repo:
        packagerepo_in_tmp_path.testing_debug = None

    settings.Settings.create_repository_directories(repositories=[packagerepo_in_tmp_path])
    assert packagerepo_in_tmp_path._stable_repo_dir.exists()  # nosec: B101
    assert packagerepo_in_tmp_path._stable_source_repo_dir.exists()  # nosec: B101
    assert packagerepo_in_tmp_path._package_pool_dir.exists()  # nosec: B101
    assert packagerepo_in_tmp_path._source_pool_dir.exists()  # nosec: B101
    assert packagerepo_in_tmp_path._stable_management_repo_dir.exists()  # nosec: B101

    if debug_repo:
        assert packagerepo_in_tmp_path._debug_repo_dir.exists()  # nosec: B101
        assert packagerepo_in_tmp_path._debug_source_repo_dir.exists()  # nosec: B101
        assert packagerepo_in_tmp_path._debug_management_repo_dir.exists()  # nosec: B101
    if staging_repo:
        assert packagerepo_in_tmp_path._staging_repo_dir.exists()  # nosec: B101
        assert packagerepo_in_tmp_path._staging_source_repo_dir.exists()  # nosec: B101
        assert packagerepo_in_tmp_path._staging_management_repo_dir.exists()  # nosec: B101
        if staging_debug_repo:
            assert packagerepo_in_tmp_path._staging_debug_repo_dir.exists()  # nosec: B101
            assert packagerepo_in_tmp_path._staging_debug_source_repo_dir.exists()  # nosec: B101
            assert packagerepo_in_tmp_path._staging_debug_management_repo_dir.exists()  # nosec: B101
    if testing_repo:
        assert packagerepo_in_tmp_path._testing_repo_dir.exists()  # nosec: B101
        assert packagerepo_in_tmp_path._testing_source_repo_dir.exists()  # nosec: B101
        assert packagerepo_in_tmp_path._testing_management_repo_dir.exists()  # nosec: B101
        if testing_debug_repo:
            assert packagerepo_in_tmp_path._testing_debug_repo_dir.exists()  # nosec: B101
            assert packagerepo_in_tmp_path._testing_debug_source_repo_dir.exists()  # nosec: B101
            assert packagerepo_in_tmp_path._testing_debug_management_repo_dir.exists()  # nosec: B101


@mark.parametrize(
    "repo1_overrides, repo2_overrides, expectation",
    [
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            does_not_raise(),
        ),
        (
            {},
            {
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            does_not_raise(),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            does_not_raise(),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {},
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
            },
            raises(ValueError),
        ),
        (
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2/default1"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug/default1"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging/default1-staging"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug/default1-staging-debug"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing/default1-testing"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug/testing1-testing-debug"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "package_pool_dir": Path("/repo/pkg/pool/pkg/default1"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "source_pool_dir": Path("/repo/pkg/pool/src/default1"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "stable_repo_dir": Path("/repo/pkg/repo/default2/default1"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug/default1-debug"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging/default1-staging"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug/default1-staging-debug"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing/default1-testing"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
        (
            {
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug/default1-testing-debug"),
            },
            {
                "stable_management_repo_dir": Path("/repo/mgmt/default2"),
                "debug_management_repo_dir": Path("/repo/mgmt/default2-debug"),
                "staging_management_repo_dir": Path("/repo/mgmt/default2-staging"),
                "staging_debug_management_repo_dir": Path("/repo/mgmt/default2-staging-debug"),
                "testing_management_repo_dir": Path("/repo/mgmt/default2-testing"),
                "testing_debug_management_repo_dir": Path("/repo/mgmt/default2-testing-debug"),
                "package_pool_dir": Path("/repo/pkg/pool/pkg"),
                "source_pool_dir": Path("/repo/pkg/pool/src"),
                "stable_repo_dir": Path("/repo/pkg/repo/default2"),
                "debug_repo_dir": Path("/repo/pkg/repo/default2-debug"),
                "staging_repo_dir": Path("/repo/pkg/repo/default2-staging"),
                "staging_debug_repo_dir": Path("/repo/pkg/repo/default2-staging-debug"),
                "testing_repo_dir": Path("/repo/pkg/repo/default2-testing"),
                "testing_debug_repo_dir": Path("/repo/pkg/repo/default2-testing-debug"),
            },
            raises(ValueError),
        ),
    ],
    ids=[
        "no duplication",
        "duplicate stable management repository dir",
        "duplicate stable debug management repository dir",
        "duplicate staging management repository dir",
        "duplicate staging debug management repository dir",
        "duplicate testing management repository dir",
        "duplicate testing debug management repository dir",
        "duplicate package pool dir",
        "duplicate source pool dir",
        "duplicate stable repo dir",
        "duplicate stable debug repo dir",
        "duplicate staging repo dir",
        "duplicate staging debug repo dir",
        "duplicate testing repo dir",
        "duplicate testing debug repo dir",
        "nested stable management repository dir",
        "nested stable debug management repository dir",
        "nested staging management repository dir",
        "nested staging debug management repository dir",
        "nested testing management repository dir",
        "nested testing debug management repository dir",
        "nested package pool dir",
        "nested source pool dir",
        "nested stable repo dir",
        "nested stable debug repo dir",
        "nested staging repo dir",
        "nested staging debug repo dir",
        "nested testing repo dir",
        "nested testing debug repo dir",
    ],
)
def test_ensure_non_overlapping_repositories(
    repo1_overrides: dict[str, Path],
    repo2_overrides: dict[str, Path],
    expectation: ContextManager[str],
    usersettings: settings.Settings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    packagerepo1 = usersettings.repositories[0]
    packagerepo2 = deepcopy(usersettings.repositories[0])

    packagerepo1._stable_management_repo_dir = (
        repo1_overrides.get("stable_management_repo_dir") or packagerepo1._stable_management_repo_dir
    )
    packagerepo1._debug_management_repo_dir = (
        repo1_overrides.get("debug_management_repo_dir") or packagerepo1._debug_management_repo_dir
    )
    packagerepo1._staging_management_repo_dir = (
        repo1_overrides.get("staging_management_repo_dir") or packagerepo1._staging_management_repo_dir
    )
    packagerepo1._staging_debug_management_repo_dir = (
        repo1_overrides.get("staging_debug_management_repo_dir") or packagerepo1._staging_debug_management_repo_dir
    )
    packagerepo1._testing_management_repo_dir = (
        repo1_overrides.get("testing_management_repo_dir") or packagerepo1._testing_management_repo_dir
    )
    packagerepo1._testing_debug_management_repo_dir = (
        repo1_overrides.get("testing_debug_management_repo_dir") or packagerepo1._testing_debug_management_repo_dir
    )
    packagerepo1._package_pool_dir = repo1_overrides.get("package_pool_dir") or packagerepo1._package_pool_dir
    packagerepo1._source_pool_dir = repo1_overrides.get("source_pool_dir") or packagerepo1._source_pool_dir
    packagerepo1._stable_repo_dir = repo1_overrides.get("stable_repo_dir") or packagerepo1._stable_repo_dir
    packagerepo1._debug_repo_dir = repo1_overrides.get("debug_repo_dir") or packagerepo1._debug_repo_dir
    packagerepo1._staging_repo_dir = repo1_overrides.get("staging_repo_dir") or packagerepo1._staging_repo_dir
    packagerepo1._staging_debug_repo_dir = (
        repo1_overrides.get("staging_debug_repo_dir") or packagerepo1._staging_debug_repo_dir
    )
    packagerepo1._testing_repo_dir = repo1_overrides.get("testing_repo_dir") or packagerepo1._testing_repo_dir
    packagerepo1._testing_debug_repo_dir = (
        repo1_overrides.get("testing_debug_repo_dir") or packagerepo1._testing_debug_repo_dir
    )

    packagerepo2._stable_management_repo_dir = (
        repo2_overrides.get("stable_management_repo_dir") or packagerepo1._stable_management_repo_dir
    )
    packagerepo2._debug_management_repo_dir = (
        repo2_overrides.get("debug_management_repo_dir") or packagerepo1._debug_management_repo_dir
    )
    packagerepo2._staging_management_repo_dir = (
        repo2_overrides.get("staging_management_repo_dir") or packagerepo1._staging_management_repo_dir
    )
    packagerepo2._staging_debug_management_repo_dir = (
        repo2_overrides.get("staging_debug_management_repo_dir") or packagerepo1._staging_debug_management_repo_dir
    )
    packagerepo2._testing_management_repo_dir = (
        repo2_overrides.get("testing_management_repo_dir") or packagerepo1._testing_management_repo_dir
    )
    packagerepo2._testing_debug_management_repo_dir = (
        repo2_overrides.get("testing_debug_management_repo_dir") or packagerepo1._testing_debug_management_repo_dir
    )
    packagerepo2._package_pool_dir = repo2_overrides.get("package_pool_dir") or packagerepo1._package_pool_dir
    packagerepo2._source_pool_dir = repo2_overrides.get("source_pool_dir") or packagerepo1._source_pool_dir
    packagerepo2._stable_repo_dir = repo2_overrides.get("stable_repo_dir") or packagerepo1._stable_repo_dir
    packagerepo2._debug_repo_dir = repo2_overrides.get("debug_repo_dir") or packagerepo1._debug_repo_dir
    packagerepo2._staging_repo_dir = repo2_overrides.get("staging_repo_dir") or packagerepo1._staging_repo_dir
    packagerepo2._staging_debug_repo_dir = (
        repo2_overrides.get("staging_debug_repo_dir") or packagerepo1._staging_debug_repo_dir
    )
    packagerepo2._testing_repo_dir = repo2_overrides.get("testing_repo_dir") or packagerepo1._testing_repo_dir
    packagerepo2._testing_debug_repo_dir = (
        repo2_overrides.get("testing_debug_repo_dir") or packagerepo1._testing_debug_repo_dir
    )

    debug(f"PackageRepo 1 before test: {packagerepo1.archiving}")
    debug(f"PackageRepo 2 before test: {packagerepo2.archiving}")
    with expectation:
        usersettings.ensure_non_overlapping_repositories(repositories=[packagerepo1, packagerepo2])


@mark.parametrize(
    "settings_type, expectation",
    [
        (SettingsTypeEnum.SYSTEM, does_not_raise()),
        (SettingsTypeEnum.USER, does_not_raise()),
        (Mock(value="foo"), raises(RuntimeError)),
    ],
)
def test_get_default_managementrepo(
    settings_type: SettingsTypeEnum,
    expectation: ContextManager[str],
    tmp_path: Path,
) -> None:
    package_pool_base = tmp_path / "package_pool_base"
    package_pool_base.mkdir()
    source_pool_base = tmp_path / "source_pool_base"
    source_pool_base.mkdir()
    with patch("repod.config.settings.PACKAGE_POOL_BASE", {settings_type: package_pool_base}):
        with patch("repod.config.settings.SOURCE_POOL_BASE", {settings_type: source_pool_base}):
            with expectation:
                assert isinstance(  # nosec: B101
                    settings.get_default_managementrepo(settings_type=settings_type),
                    settings.ManagementRepo,
                )


@mark.parametrize(
    "settings_type, expectation",
    [
        (SettingsTypeEnum.SYSTEM, does_not_raise()),
        (SettingsTypeEnum.USER, does_not_raise()),
        (Mock(value="foo"), raises(RuntimeError)),
    ],
)
def test_get_default_packagerepo(
    settings_type: SettingsTypeEnum,
    expectation: ContextManager[str],
    tmp_path: Path,
) -> None:
    package_pool_base = tmp_path / "package_pool_base"
    package_pool_base.mkdir()
    source_pool_base = tmp_path / "source_pool_base"
    source_pool_base.mkdir()
    with patch("repod.config.settings.PACKAGE_POOL_BASE", {settings_type: package_pool_base}):
        with patch("repod.config.settings.SOURCE_POOL_BASE", {settings_type: source_pool_base}):
            with expectation:
                assert isinstance(  # nosec: B101
                    settings.get_default_packagerepo(settings_type=settings_type),
                    settings.PackageRepo,
                )


@mark.parametrize(
    "path, path_name, other, other_name, expectation",
    [
        (Path("foo"), "foo", Path("bar"), "bar", does_not_raise()),
        (Path("foo"), "foo", Path("foo"), "bar", raises(ValueError)),
    ],
)
def test_raise_on_path_equals_other(
    path: Path, path_name: str, other: Path, other_name: str, expectation: ContextManager[str]
) -> None:
    with expectation:
        settings.raise_on_path_equals_other(path=path, path_name=path_name, other=other, other_name=other_name)


@mark.parametrize(
    "path, path_name, other, other_name, expectation",
    [
        (Path("/foo"), "foo", Path("/bar"), "bar", does_not_raise()),
        (Path("/foo"), "foo", Path("/foo-bar"), "bar", does_not_raise()),
        (Path("/bar/foo"), "foo", Path("/bar"), "bar", raises(ValueError)),
    ],
)
def test_raise_on_path_in_other(
    path: Path, path_name: str, other: Path, other_name: str, expectation: ContextManager[str]
) -> None:
    with expectation:
        settings.raise_on_path_in_other(path=path, path_name=path_name, other=other, other_name=other_name)


@mark.parametrize(
    "path, path_name, path_list, other_name, expectation",
    [
        (Path("/foo"), "foo", [], "bar", does_not_raise()),
        (Path("/foo"), "foo", [Path("/bar")], "bar", does_not_raise()),
        (Path("/foo"), "foo", [Path("/foo")], "bar", raises(ValueError)),
        (Path("/foo/bar"), "foo", [Path("/foo")], "bar", raises(ValueError)),
    ],
)
def test_raise_on_path_in_list_of_paths(
    path: Path | None,
    path_name: str,
    path_list: list[Path],
    other_name: str,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        settings.raise_on_path_in_list_of_paths(
            path=path,
            path_name=path_name,
            path_list=path_list,
            other_name=other_name,
        )


@mark.parametrize(
    "repo_dirs, repo_dir_name, repo_dir_options, self_dup_ok, self_nested_ok, expectation",
    [
        ([Path("/foo")], "foo", [([Path("/bar")], "bar")], False, False, does_not_raise()),
        ([Path("/foo")], "foo", [([Path("/foo")], "bar")], False, False, raises(ValueError)),
        ([Path("/foo"), Path("/foo")], "foo", [([Path("/bar")], "bar")], False, False, raises(ValueError)),
        ([Path("/foo"), Path("/foo")], "foo", [([Path("/bar")], "bar")], True, False, does_not_raise()),
        ([Path("/foo"), Path("/foo/bar")], "foo", [([Path("/bar")], "bar")], False, False, raises(ValueError)),
        ([Path("/foo"), Path("/foo/bar")], "foo", [([Path("/bar")], "bar")], False, True, does_not_raise()),
    ],
)
def test_validate_repo_paths(
    repo_dirs: list[Path],
    repo_dir_name: str,
    repo_dir_options: list[tuple[list[Path], str]],
    self_dup_ok: bool,
    self_nested_ok: bool,
    expectation: ContextManager[str],
) -> None:
    with expectation:
        settings.validate_repo_paths(
            repo_dirs=repo_dirs,
            repo_dir_name=repo_dir_name,
            repo_dir_options=repo_dir_options,
            self_dup_ok=self_dup_ok,
            self_nested_ok=self_nested_ok,
        )


@mark.parametrize(
    "path, base_path, output, expectation",
    [
        (Path("bar"), Path("/foo"), Path("/foo/bar"), does_not_raise()),
        (Path("/foo/bar"), Path("/foo"), Path("/foo/bar"), does_not_raise()),
        (Path("/foo/bar"), Path("foo"), Path("/foo/bar"), raises(ValueError)),
    ],
)
def test_to_absolute_path(path: Path, base_path: Path, output: Path, expectation: ContextManager[str]) -> None:
    with expectation:
        assert settings.to_absolute_path(path=path, base_path=base_path) == output  # nosec: B101


@mark.parametrize(
    "dir_exists, mkdir_raises, dir_is_dir, dir_writable, expectation",
    [
        (True, False, True, True, does_not_raise()),
        (True, False, True, False, raises(ValueError)),
        (True, False, False, True, raises(ValueError)),
        (False, False, True, True, does_not_raise()),
        (False, True, True, True, raises(ValueError)),
    ],
)
def test_create_and_validate_directory(
    dir_exists: bool,
    mkdir_raises: bool,
    dir_is_dir: bool,
    dir_writable: bool,
    expectation: ContextManager[str],
    tmp_path: Path,
) -> None:

    directory = tmp_path / "directory"
    if dir_is_dir:
        if dir_exists:
            directory.mkdir()
    else:
        if dir_exists:
            directory.touch()

    if mkdir_raises:
        with patch("repod.config.settings.Path.mkdir", Mock(side_effect=PermissionError)):
            with expectation:
                settings.create_and_validate_directory(directory=directory)
    else:
        if not dir_writable:
            with patch("os.access", Mock(return_value=False)):
                with expectation:
                    settings.create_and_validate_directory(directory=directory)
        else:
            with expectation:
                settings.create_and_validate_directory(directory=directory)


@mark.parametrize(
    "has_repo, has_namesake_repo, reuse_first_repo_name, architecture, expectation",
    [
        (True, False, True, settings.DEFAULT_ARCHITECTURE, does_not_raise()),
        (True, True, True, settings.DEFAULT_ARCHITECTURE, does_not_raise()),
        (True, True, True, ArchitectureEnum.ARM, does_not_raise()),
        (True, True, True, None, raises(RuntimeError)),
        (True, True, False, ArchitectureEnum.ARM, raises(RuntimeError)),
        (False, False, True, settings.DEFAULT_ARCHITECTURE, raises(RuntimeError)),
        (False, False, False, None, raises(RuntimeError)),
    ],
)
def test_settings_get_repo(
    has_repo: bool,
    has_namesake_repo: bool,
    reuse_first_repo_name: bool,
    architecture: ArchitectureEnum | None,
    expectation: ContextManager[str],
    usersettings: settings.UserSettings,
) -> None:
    name = Path("foo")

    if reuse_first_repo_name:
        name = usersettings.repositories[0].name
    if not has_repo:
        usersettings.repositories = []
    else:
        if has_namesake_repo:
            namesake = deepcopy(usersettings.repositories[0])
            namesake.architecture = ArchitectureEnum.ARM
            usersettings.repositories.append(namesake)

    with expectation:
        usersettings.get_repo(name=name, architecture=architecture)


def test_settings_get_repo_management_repo(usersettings: settings.UserSettings) -> None:
    assert isinstance(  # nosec: B101
        usersettings.get_repo_management_repo(
            name=Path(settings.DEFAULT_NAME),
            architecture=settings.DEFAULT_ARCHITECTURE,
        ),
        settings.ManagementRepo,
    )


def test_settings_get_repo_architecture(usersettings: settings.UserSettings) -> None:
    assert isinstance(  # nosec: B101
        usersettings.get_repo_architecture(
            name=Path(settings.DEFAULT_NAME),
            architecture=settings.DEFAULT_ARCHITECTURE,
        ),
        ArchitectureEnum,
    )


def test_settings_get_repo_database_compression(usersettings: settings.UserSettings) -> None:
    assert isinstance(  # nosec: B101
        usersettings.get_repo_database_compression(
            name=Path(settings.DEFAULT_NAME),
            architecture=settings.DEFAULT_ARCHITECTURE,
        ),
        CompressionTypeEnum,
    )


@mark.parametrize("add_group", [(True), (False)])
def test_settings_get_repos_by_group(add_group: bool, usersettings: settings.UserSettings) -> None:
    if add_group:
        usersettings.repositories[0].group = 1

    usersettings.get_repos_by_group(group=1 if add_group else None)


@mark.parametrize(
    (
        "repo_dir_type, debug_exists, staging_exists, staging_debug_exists, "
        "testing_exists, testing_debug_exists, repo_type, expectation"
    ),
    [
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, RepoTypeEnum.STABLE, does_not_raise()),
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, RepoTypeEnum.STABLE_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, RepoTypeEnum.STAGING, does_not_raise()),
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, RepoTypeEnum.STAGING_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, RepoTypeEnum.TESTING, does_not_raise()),
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, RepoTypeEnum.TESTING_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.MANAGEMENT, False, True, False, True, False, RepoTypeEnum.STABLE_DEBUG, raises(RuntimeError)),
        (
            RepoDirTypeEnum.MANAGEMENT,
            False,
            False,
            False,
            True,
            False,
            RepoTypeEnum.STAGING_DEBUG,
            raises(RuntimeError),
        ),
        (RepoDirTypeEnum.MANAGEMENT, False, True, False, True, False, RepoTypeEnum.STAGING_DEBUG, raises(RuntimeError)),
        (
            RepoDirTypeEnum.MANAGEMENT,
            False,
            True,
            False,
            False,
            False,
            RepoTypeEnum.TESTING_DEBUG,
            raises(RuntimeError),
        ),
        (RepoDirTypeEnum.MANAGEMENT, False, True, False, True, False, RepoTypeEnum.TESTING_DEBUG, raises(RuntimeError)),
        (RepoDirTypeEnum.MANAGEMENT, True, False, False, True, True, RepoTypeEnum.STAGING, raises(RuntimeError)),
        (
            RepoDirTypeEnum.MANAGEMENT,
            True,
            True,
            True,
            False,
            False,
            RepoTypeEnum.TESTING,
            raises(RuntimeError),
        ),
        (RepoDirTypeEnum.MANAGEMENT, True, True, True, True, True, None, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, RepoTypeEnum.STABLE, does_not_raise()),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, RepoTypeEnum.STABLE_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, RepoTypeEnum.STAGING, does_not_raise()),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, RepoTypeEnum.STAGING_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, RepoTypeEnum.TESTING, does_not_raise()),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, RepoTypeEnum.TESTING_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.PACKAGE, False, True, False, True, False, RepoTypeEnum.STABLE_DEBUG, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, False, False, True, True, RepoTypeEnum.STAGING, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, False, False, True, True, RepoTypeEnum.STAGING_DEBUG, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, True, False, True, True, RepoTypeEnum.STAGING_DEBUG, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, True, True, False, False, RepoTypeEnum.TESTING, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, True, True, False, False, RepoTypeEnum.TESTING_DEBUG, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, False, RepoTypeEnum.TESTING_DEBUG, raises(RuntimeError)),
        (RepoDirTypeEnum.PACKAGE, True, True, True, True, True, None, raises(RuntimeError)),
        (RepoDirTypeEnum.POOL, False, False, False, False, False, RepoTypeEnum.STABLE, does_not_raise()),
        (RepoDirTypeEnum.POOL, False, False, False, False, False, RepoTypeEnum.STABLE_DEBUG, does_not_raise()),
        (RepoDirTypeEnum.POOL, False, False, False, False, False, RepoTypeEnum.STAGING, does_not_raise()),
        (RepoDirTypeEnum.POOL, False, False, False, False, False, RepoTypeEnum.TESTING, does_not_raise()),
        (RepoDirTypeEnum.POOL, False, False, False, False, False, None, does_not_raise()),
        (None, True, True, True, True, True, RepoTypeEnum.STABLE, raises(RuntimeError)),
        (None, True, True, True, True, True, None, raises(RuntimeError)),
    ],
)
def test_settings_get_repo_path(
    repo_dir_type: RepoDirTypeEnum,
    debug_exists: bool,
    staging_exists: bool,
    staging_debug_exists: bool,
    testing_exists: bool,
    testing_debug_exists: bool,
    repo_type: RepoTypeEnum,
    expectation: ContextManager[str],
    usersettings: settings.UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    if not debug_exists:
        usersettings.repositories[0].debug = None

    if not staging_exists:
        usersettings.repositories[0].staging = None

    if not staging_debug_exists:
        usersettings.repositories[0].staging_debug = None

    if not testing_exists:
        usersettings.repositories[0].testing = None

    if not testing_debug_exists:
        usersettings.repositories[0].testing_debug = None

    with expectation:
        path = usersettings.get_repo_path(
            repo_dir_type=repo_dir_type,
            name=Path(settings.DEFAULT_NAME),
            architecture=settings.DEFAULT_ARCHITECTURE,
            repo_type=repo_type,
        )

        match repo_dir_type, repo_type:
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STABLE:
                assert path == usersettings.repositories[0]._stable_management_repo_dir  # nosec: B101
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STABLE_DEBUG:
                assert path == usersettings.repositories[0]._debug_management_repo_dir  # nosec: B101
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STAGING:
                assert path == usersettings.repositories[0]._staging_management_repo_dir  # nosec: B101
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STAGING_DEBUG:
                assert path == usersettings.repositories[0]._staging_debug_management_repo_dir  # nosec: B101
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.TESTING:
                assert path == usersettings.repositories[0]._testing_management_repo_dir  # nosec: B101
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.TESTING_DEBUG:
                assert path == usersettings.repositories[0]._testing_debug_management_repo_dir  # nosec: B101
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STABLE:
                assert path == usersettings.repositories[0]._stable_repo_dir  # nosec: B101
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STABLE_DEBUG:
                assert path == usersettings.repositories[0]._debug_repo_dir  # nosec: B101
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STAGING:
                assert path == usersettings.repositories[0]._staging_repo_dir  # nosec: B101
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STAGING_DEBUG:
                assert path == usersettings.repositories[0]._staging_debug_repo_dir  # nosec: B101
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.TESTING:
                assert path == usersettings.repositories[0]._testing_repo_dir  # nosec: B101
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.TESTING_DEBUG:
                assert path == usersettings.repositories[0]._testing_debug_repo_dir  # nosec: B101
            case RepoDirTypeEnum.POOL, _:
                assert path == usersettings.repositories[0]._package_pool_dir  # nosec: B101


@mark.parametrize(
    "repo_type, has_debug, has_staging, has_testing, expectation",
    [
        (RepoTypeEnum.STABLE, True, True, True, does_not_raise()),
        (RepoTypeEnum.STABLE, False, True, True, does_not_raise()),
        (RepoTypeEnum.STABLE, False, False, True, does_not_raise()),
        (RepoTypeEnum.STABLE, False, False, False, does_not_raise()),
        (RepoTypeEnum.STABLE_DEBUG, True, True, True, does_not_raise()),
        (RepoTypeEnum.STABLE_DEBUG, True, False, True, does_not_raise()),
        (RepoTypeEnum.STABLE_DEBUG, True, False, False, does_not_raise()),
        (RepoTypeEnum.STABLE_DEBUG, True, True, False, does_not_raise()),
        (RepoTypeEnum.STABLE_DEBUG, False, True, True, raises(RuntimeError)),
        (RepoTypeEnum.STABLE_DEBUG, False, False, True, raises(RuntimeError)),
        (RepoTypeEnum.STABLE_DEBUG, False, False, False, raises(RuntimeError)),
        (RepoTypeEnum.STAGING, True, True, True, does_not_raise()),
        (RepoTypeEnum.STAGING, True, True, False, does_not_raise()),
        (RepoTypeEnum.STAGING, False, True, False, does_not_raise()),
        (RepoTypeEnum.STAGING, False, False, False, raises(RuntimeError)),
        (RepoTypeEnum.STAGING, False, False, True, raises(RuntimeError)),
        (RepoTypeEnum.STAGING, True, False, False, raises(RuntimeError)),
        (RepoTypeEnum.STAGING, True, False, True, raises(RuntimeError)),
        (RepoTypeEnum.STAGING_DEBUG, True, True, True, does_not_raise()),
        (RepoTypeEnum.STAGING_DEBUG, True, True, False, does_not_raise()),
        (RepoTypeEnum.STAGING_DEBUG, False, False, False, raises(RuntimeError)),
        (RepoTypeEnum.STAGING_DEBUG, False, True, False, raises(RuntimeError)),
        (RepoTypeEnum.STAGING_DEBUG, False, False, True, raises(RuntimeError)),
        (RepoTypeEnum.STAGING_DEBUG, True, False, True, raises(RuntimeError)),
        (RepoTypeEnum.TESTING, True, True, True, does_not_raise()),
        (RepoTypeEnum.TESTING, True, False, True, does_not_raise()),
        (RepoTypeEnum.TESTING, False, False, True, does_not_raise()),
        (RepoTypeEnum.TESTING, False, True, True, does_not_raise()),
        (RepoTypeEnum.TESTING, False, False, False, raises(RuntimeError)),
        (RepoTypeEnum.TESTING, True, False, False, raises(RuntimeError)),
        (RepoTypeEnum.TESTING, True, True, False, raises(RuntimeError)),
        (RepoTypeEnum.TESTING, False, True, False, raises(RuntimeError)),
        (RepoTypeEnum.TESTING_DEBUG, True, True, True, does_not_raise()),
        (RepoTypeEnum.TESTING_DEBUG, True, False, True, does_not_raise()),
        (RepoTypeEnum.TESTING_DEBUG, False, False, True, raises(RuntimeError)),
        (RepoTypeEnum.TESTING_DEBUG, False, True, True, raises(RuntimeError)),
        (RepoTypeEnum.TESTING_DEBUG, True, True, False, raises(RuntimeError)),
        (RepoTypeEnum.TESTING_DEBUG, True, False, False, raises(RuntimeError)),
        (None, True, True, True, raises(RuntimeError)),
    ],
)
def test_settings_get_management_repo_stability_paths(
    repo_type: RepoTypeEnum,
    has_debug: bool,
    has_staging: bool,
    has_testing: bool,
    expectation: ContextManager[str],
    usersettings: settings.UserSettings,
    caplog: LogCaptureFixture,
) -> None:
    if not has_debug:
        usersettings.repositories[0].debug = None

    if not has_staging:
        usersettings.repositories[0].staging = None

    if not has_testing:
        usersettings.repositories[0].testing = None

    with expectation:
        return_value = usersettings.get_management_repo_stability_paths(
            name=Path(settings.DEFAULT_NAME),
            architecture=settings.DEFAULT_ARCHITECTURE,
            repo_type=repo_type,
        )

        match repo_type:
            case RepoTypeEnum.STABLE:
                paths_above = []
                paths_above += [usersettings.repositories[0]._staging_management_repo_dir] if has_staging else []
                paths_above += [usersettings.repositories[0]._testing_management_repo_dir] if has_testing else []

                assert (paths_above, []) == return_value  # nosec: B101
            case RepoTypeEnum.STABLE_DEBUG:
                paths_above = []
                paths_above += [usersettings.repositories[0]._staging_debug_management_repo_dir] if has_staging else []
                paths_above += [usersettings.repositories[0]._testing_debug_management_repo_dir] if has_testing else []

                assert (paths_above, []) == return_value  # nosec: B101
            case RepoTypeEnum.STAGING:
                paths_below = [usersettings.repositories[0]._stable_management_repo_dir]
                paths_below += [usersettings.repositories[0]._testing_management_repo_dir] if has_testing else []

                assert ([], paths_below) == return_value  # nosec: B101
            case RepoTypeEnum.STAGING_DEBUG:
                paths_below = [usersettings.repositories[0]._debug_management_repo_dir]
                paths_below += [usersettings.repositories[0]._testing_debug_management_repo_dir] if has_testing else []

                assert ([], paths_below) == return_value  # nosec: B101
            case RepoTypeEnum.TESTING:
                paths_above = []
                paths_above += [usersettings.repositories[0]._staging_management_repo_dir] if has_staging else []

                assert (  # nosec: B101
                    paths_above,
                    [usersettings.repositories[0]._stable_management_repo_dir],
                ) == return_value
            case RepoTypeEnum.TESTING_DEBUG:
                paths_above = []
                paths_above += [usersettings.repositories[0]._staging_debug_management_repo_dir] if has_staging else []

                assert (  # nosec: B101
                    paths_above,
                    [usersettings.repositories[0]._debug_management_repo_dir],
                ) == return_value


@mark.parametrize(
    "urls, tls_required, expectation",
    [
        (["https://foobar.io/some/where"], True, does_not_raise()),
        (["http://foobar.io/some/where"], False, does_not_raise()),
        (["http://foobar.io/some/where"], True, raises(ValueError)),
        (["foo"], True, raises(ValueError)),
        (["foo"], False, raises(ValueError)),
    ],
)
def test_urlvalidationsettings(
    urls: list[str],
    tls_required: bool,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    with expectation:
        settings.UrlValidationSettings(urls=urls, tls_required=tls_required)


@mark.parametrize(
    "validator, url, return_value",
    [
        (
            settings.UrlValidationSettings(urls=["https://foobar.io/"], tls_required=True),
            AnyUrl(url="https://foobar.io/bar/baz", scheme="https"),
            True,
        ),
        (
            settings.UrlValidationSettings(urls=["https://foobar.io/"], tls_required=True),
            AnyUrl(url="http://foobar.io/bar/baz", scheme="http"),
            False,
        ),
        (
            settings.UrlValidationSettings(urls=["https://foobar.io/beh/"], tls_required=True),
            AnyUrl(url="https://foobar.io/bar/baz", scheme="https"),
            False,
        ),
    ],
)
def test_urlvalidationsettings_validate_url(
    validator: settings.UrlValidationSettings,
    url: AnyUrl,
    return_value: bool,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    assert validator.validate_url(url=url) == return_value  # nosec: B101


@mark.parametrize(
    (
        "packages, sources, expanduser_raises, expanduser_absolute, "
        "expectation, packages_return_value, sources_return_value"
    ),
    [
        (Path("/packages"), Path("/sources"), False, True, does_not_raise(), Path("/packages"), Path("/sources")),
        (Path("~/packages"), Path("~/sources"), False, True, does_not_raise(), Path("/expanded"), Path("/expanded")),
        (Path("~/packages"), Path("~/sources"), False, False, raises(ValueError), None, None),
        (Path("~/packages"), Path("~/sources"), True, True, raises(ValueError), None, None),
        (Path("/packages"), Path("sources"), False, True, raises(ValueError), None, None),
        (Path("packages"), Path("/sources"), False, True, raises(ValueError), None, None),
    ],
)
@patch("repod.config.settings.Path.expanduser")
def test_archivesettings_validate_packages(
    expanduser_mock: Mock,
    packages: Path,
    sources: Path,
    expanduser_raises: bool,
    expanduser_absolute: bool,
    expectation: ContextManager[str],
    packages_return_value: bool,
    sources_return_value: bool,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    if expanduser_absolute:
        expanduser_mock.return_value = Path("/expanded")
    else:
        expanduser_mock.return_value = Path("expanded")

    if expanduser_raises:
        expanduser_mock.side_effect = RuntimeError

    with expectation:
        archiving = settings.ArchiveSettings(packages=packages, sources=sources)

        assert packages_return_value == archiving.packages  # nosec: B101
        assert sources_return_value == archiving.sources  # nosec: B101


@mark.parametrize(
    "settings_type, expectation",
    [
        (SettingsTypeEnum.USER, does_not_raise()),
        (SettingsTypeEnum.SYSTEM, does_not_raise()),
        (None, raises(RuntimeError)),
    ],
)
def test_get_default_archive_settings(settings_type: SettingsTypeEnum, expectation: ContextManager[str]) -> None:
    with expectation:
        settings.get_default_archive_settings(settings_type=settings_type)
