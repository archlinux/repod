from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from logging import DEBUG
from pathlib import Path
from typing import ContextManager, Dict, Optional
from unittest.mock import Mock, call, patch

from pytest import LogCaptureFixture, mark, raises

from repod.common.enums import ArchitectureEnum, RepoTypeEnum, SettingsTypeEnum
from repod.config import settings


def test_architecture_validate_architecture(default_arch: str) -> None:
    assert settings.Architecture(architecture=default_arch)

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
        assert settings.ManagementRepo(
            directory=empty_dir,
            url=url,
        )


@mark.parametrize(
    "name, debug_repo, staging_repo, testing_repo, package_pool, source_pool, management_repo, url, expectation",
    [
        (Path("foo"), None, None, None, False, False, False, None, does_not_raise()),
        (Path("foo"), Path("debug"), None, None, False, False, False, None, does_not_raise()),
        (Path("foo"), Path("debug"), Path("staging"), None, False, False, False, None, does_not_raise()),
        (Path("foo"), Path("debug"), Path("staging"), Path("testing"), False, False, False, None, does_not_raise()),
        ("foo", None, None, None, False, False, False, None, does_not_raise()),
        ("foo", "debug", None, None, False, False, False, None, does_not_raise()),
        ("foo", "debug", "staging", None, False, False, False, None, does_not_raise()),
        ("foo", "debug", "staging", "testing", False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), None, None, None, False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), Path("debug"), None, None, False, False, False, None, does_not_raise()),
        (Path("foo-bar123"), Path("debug"), Path("staging"), None, False, False, False, None, does_not_raise()),
        (
            Path("foo-bar123"),
            Path("debug"),
            Path("staging"),
            Path("testing"),
            False,
            False,
            False,
            None,
            does_not_raise(),
        ),
        (Path("foo-bar123"), None, None, None, False, False, True, "https://foo.bar", does_not_raise()),
        (Path("foo-bar123"), Path("debug"), None, None, False, False, True, "https://foo.bar", does_not_raise()),
        (
            Path("foo-bar123"),
            Path("debug"),
            Path("staging"),
            None,
            False,
            False,
            True,
            "https://foo.bar",
            does_not_raise(),
        ),
        (
            Path("foo-bar123"),
            Path("debug"),
            Path("staging"),
            Path("testing"),
            False,
            False,
            True,
            "https://foo.bar",
            does_not_raise(),
        ),
        (Path(" foo"), None, None, None, False, False, False, None, raises(ValueError)),
        (Path("foo"), Path(" debug"), None, None, False, False, False, None, raises(ValueError)),
        (Path("foo"), Path("debug "), Path(" staging"), None, False, False, False, None, raises(ValueError)),
        (
            Path("foo"),
            Path("debug "),
            Path(" staging"),
            Path(" testing"),
            False,
            False,
            False,
            None,
            raises(ValueError),
        ),
        (Path("foo"), Path("foo"), None, None, False, False, False, None, raises(ValueError)),
        (Path("foo"), None, Path("foo"), None, False, False, False, None, raises(ValueError)),
        (Path("foo"), None, None, Path("foo"), False, False, False, None, raises(ValueError)),
        (Path("foo"), Path("debug"), Path("debug"), None, False, False, False, None, raises(ValueError)),
        (Path("foo"), Path("debug"), None, Path("debug"), False, False, False, None, raises(ValueError)),
        (Path("FOO"), None, None, None, False, False, False, None, raises(ValueError)),
        (Path("FOO"), Path("debug"), None, None, False, False, False, None, raises(ValueError)),
        (Path("FOO"), Path("debug"), Path("staging"), None, False, False, False, None, raises(ValueError)),
        (Path("FOO"), Path("debug"), Path("staging"), Path("testing"), False, False, False, None, raises(ValueError)),
        (Path("foo_BAR123"), None, None, None, False, False, False, None, raises(ValueError)),
        (Path("foo_BAR123"), Path("debug"), None, None, False, False, False, None, raises(ValueError)),
        (Path("foo_BAR123"), Path("debug"), Path("staging"), None, False, False, False, None, raises(ValueError)),
        (
            Path("foo_BAR123"),
            Path("debug"),
            Path("staging"),
            Path("testing"),
            False,
            False,
            False,
            None,
            raises(ValueError),
        ),
        (Path(".foo"), None, None, None, False, False, False, None, raises(ValueError)),
        (Path(".foo"), Path("debug"), None, None, False, False, False, None, raises(ValueError)),
        (Path(".foo"), Path("debug"), Path("staging"), None, False, False, False, None, raises(ValueError)),
        (Path(".foo"), Path("debug"), Path("staging"), Path("testing"), False, False, False, None, raises(ValueError)),
        (Path("-foo"), None, None, None, False, False, False, None, raises(ValueError)),
        (Path("-foo"), Path("debug"), None, None, False, False, False, None, raises(ValueError)),
        (Path("-foo"), Path("debug"), Path("staging"), None, False, False, False, None, raises(ValueError)),
        (Path("-foo"), Path("debug"), Path("staging"), Path("testing"), False, False, False, None, raises(ValueError)),
        (Path("."), None, None, None, False, False, False, None, raises(ValueError)),
        (Path("."), Path("debug"), None, None, False, False, False, None, raises(ValueError)),
        (Path("."), Path("debug"), Path("staging"), None, False, False, False, None, raises(ValueError)),
        (Path("."), Path("debug"), Path("staging"), Path("testing"), False, False, False, None, raises(ValueError)),
    ],
)
def test_package_repo(
    name: Path,
    debug_repo: Optional[Path],
    staging_repo: Optional[Path],
    testing_repo: Optional[Path],
    package_pool: bool,
    source_pool: bool,
    management_repo: bool,
    url: Optional[str],
    expectation: ContextManager[str],
    empty_dir: Path,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    with expectation:
        assert settings.PackageRepo(
            name=name,
            debug=debug_repo,
            staging=staging_repo,
            testing=testing_repo,
            package_pool=empty_dir if package_pool else None,
            source_pool=empty_dir if source_pool else None,
            management_repo=settings.ManagementRepo(
                directory=empty_dir,
                url=url,
            )
            if management_repo
            else None,
        )


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


@patch("tomli.load", return_value={})
def test_read_toml_configuration_settings_system(
    toml_load_mock: Mock,
    empty_toml_file: Path,
    empty_toml_files_in_dir: Path,
    tmp_path: Path,
) -> None:
    with patch("repod.config.settings.SETTINGS_LOCATION", {SettingsTypeEnum.SYSTEM: empty_toml_file}):
        settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
        with patch(
            "repod.config.settings.SETTINGS_OVERRIDE_LOCATION",
            {SettingsTypeEnum.SYSTEM: empty_toml_files_in_dir},
        ):
            settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
            toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))

    with patch("repod.config.settings.SETTINGS_LOCATION", {SettingsTypeEnum.SYSTEM: tmp_path / "foo.toml"}):
        settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
        with patch(
            "repod.config.settings.SETTINGS_OVERRIDE_LOCATION",
            {SettingsTypeEnum.SYSTEM: empty_toml_files_in_dir},
        ):
            settings.read_toml_configuration_settings(Mock(spec=settings.SystemSettings))
            toml_load_mock.has_calls(call([empty_toml_file] + sorted(empty_toml_files_in_dir.glob("*.toml"))))


@mark.parametrize(
    "has_managementrepo, has_repositories",
    [
        (True, True),
        (False, False),
    ],
)
@patch("repod.config.settings.Settings.consolidate_repositories_with_defaults")
@patch("repod.config.settings.Settings.ensure_non_overlapping_repositories")
@patch("repod.config.settings.Settings.create_repository_directories")
@patch("repod.config.settings.get_default_managementrepo")
@patch("repod.config.settings.get_default_packagerepo")
def test_systemsettings(
    get_default_packagerepo_mock: Mock,
    get_default_managementrepo_mock: Mock,
    create_repository_directories_mock: Mock,
    ensure_non_overlapping_repositories_mock: Mock,
    consolidate_repositories_with_defaults_mock: Mock,
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
                            assert isinstance(conf, settings.SystemSettings)
                            assert len(conf.repositories) > 0

                            create_repository_directories_mock.assert_called_once()
                            ensure_non_overlapping_repositories_mock.assert_called_once()
                            consolidate_repositories_with_defaults_mock.assert_called_once()


@mark.parametrize(
    "has_managementrepo, has_repositories",
    [
        (True, True),
        (False, False),
    ],
)
@patch("repod.config.settings.Settings.consolidate_repositories_with_defaults")
@patch("repod.config.settings.Settings.ensure_non_overlapping_repositories")
@patch("repod.config.settings.Settings.create_repository_directories")
@patch("repod.config.settings.get_default_managementrepo")
@patch("repod.config.settings.get_default_packagerepo")
def test_usersettings(
    get_default_packagerepo_mock: Mock,
    get_default_managementrepo_mock: Mock,
    create_repository_directories_mock: Mock,
    ensure_non_overlapping_repositories_mock: Mock,
    consolidate_repositories_with_defaults_mock: Mock,
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
                            assert isinstance(conf, settings.UserSettings)
                            assert len(conf.repositories) > 0

                            create_repository_directories_mock.assert_called_once()
                            ensure_non_overlapping_repositories_mock.assert_called_once()
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
        ", repo_has_testing"
    ),
    [
        (True, True, True, True, True, True, True, True),
        (True, True, True, True, True, False, True, True),
        (True, True, True, True, True, True, False, True),
        (True, True, True, True, True, True, True, False),
        (False, False, False, False, False, False, False, False),
    ],
)
def test_settings_consolidate_repositories_with_defaults(
    repo_has_architecture: bool,
    repo_has_database_compression: bool,
    repo_has_management_repo: bool,
    repo_has_package_pool: bool,
    repo_has_source_pool: bool,
    repo_has_debug: bool,
    repo_has_staging: bool,
    repo_has_testing: bool,
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
    if not repo_has_testing:
        packagerepo_in_tmp_path.testing = None

    with patch("repod.config.settings.Settings._package_repo_base", tmp_path / "_package_repo_base"):
        with patch("repod.config.settings.Settings._source_repo_base", tmp_path / "_source_repo_base"):
            with patch("repod.config.settings.Settings._package_pool_base", tmp_path / "_package_pool_base"):
                with patch("repod.config.settings.Settings._source_pool_base", tmp_path / "_source_pool_base"):
                    with patch(
                        "repod.config.settings.Settings._management_repo_base", tmp_path / "_management_repo_base"
                    ):
                        repos = settings.Settings.consolidate_repositories_with_defaults(
                            architecture=settings.DEFAULT_ARCHITECTURE,
                            database_compression=settings.DEFAULT_DATABASE_COMPRESSION,
                            management_repo=settings.ManagementRepo(directory=tmp_path / settings.DEFAULT_NAME),
                            package_pool=tmp_path / "package_pool_dir",
                            repositories=[packagerepo_in_tmp_path],
                            source_pool=tmp_path / "source_pool_dir",
                        )

    assert (
        repos[0].architecture == packagerepo_in_tmp_path.architecture
        if repo_has_architecture
        else settings.DEFAULT_ARCHITECTURE
    )

    assert (
        repos[0].database_compression == packagerepo_in_tmp_path.database_compression
        if repo_has_database_compression
        else settings.DEFAULT_DATABASE_COMPRESSION
    )

    assert (
        repos[0].management_repo == packagerepo_in_tmp_path.management_repo
        if repo_has_management_repo
        else settings.ManagementRepo(directory=tmp_path / settings.DEFAULT_NAME)
    )

    assert (
        repos[0].package_pool == packagerepo_in_tmp_path.package_pool
        if repo_has_package_pool
        else tmp_path / "package_pool_dir"
    )

    assert (
        repos[0].source_pool == packagerepo_in_tmp_path.source_pool
        if repo_has_source_pool
        else tmp_path / "source_pool_dir"
    )


@mark.parametrize(
    "debug_repo, staging_repo, testing_repo",
    [
        (True, True, True),
        (False, True, True),
        (False, False, True),
        (False, True, False),
        (True, True, False),
        (False, False, False),
    ],
)
def test_settings_create_repository_directories(
    debug_repo: bool,
    staging_repo: bool,
    testing_repo: bool,
    packagerepo_in_tmp_path: settings.PackageRepo,
) -> None:
    if not debug_repo:
        packagerepo_in_tmp_path.debug = None
    if not staging_repo:
        packagerepo_in_tmp_path.staging = None
    if not testing_repo:
        packagerepo_in_tmp_path.testing = None

    settings.Settings.create_repository_directories(repositories=[packagerepo_in_tmp_path])
    assert packagerepo_in_tmp_path._stable_repo_dir.exists()
    assert packagerepo_in_tmp_path._stable_source_repo_dir.exists()
    assert packagerepo_in_tmp_path._package_pool_dir.exists()
    assert packagerepo_in_tmp_path._source_pool_dir.exists()
    assert packagerepo_in_tmp_path._stable_management_repo_dir.exists()

    if debug_repo:
        assert packagerepo_in_tmp_path._debug_repo_dir.exists()
        assert packagerepo_in_tmp_path._debug_source_repo_dir.exists()
        assert packagerepo_in_tmp_path._debug_management_repo_dir.exists()
    if staging_repo:
        assert packagerepo_in_tmp_path._staging_repo_dir.exists()
        assert packagerepo_in_tmp_path._staging_source_repo_dir.exists()
        assert packagerepo_in_tmp_path._staging_management_repo_dir.exists()
    if testing_repo:
        assert packagerepo_in_tmp_path._testing_repo_dir.exists()
        assert packagerepo_in_tmp_path._testing_source_repo_dir.exists()
        assert packagerepo_in_tmp_path._testing_management_repo_dir.exists()


@mark.parametrize(
    "base_overrides, repo_overrides, expectation",
    [
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
            },
            does_not_raise(),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {},
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/default/repo/source_repo_base/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "package_pool_dir": Path("/default/repo/source_repo_base/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "source_pool_dir": Path("/default/repo/source_repo_base/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/source_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/default/repo/package_repo_base/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "package_pool_dir": Path("/default/repo/package_repo_base/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "source_pool_dir": Path("/default/repo/package_repo_base/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
                "package_pool_dir": Path("/repo/stable_management_repo_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
                "source_pool_dir": Path("/repo/stable_management_repo_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/repo/stable_management_repo_dir"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/repo/stable_management_repo_dir"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
                "staging_management_repo_dir": Path("/repo/stable_management_repo_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
                "testing_management_repo_dir": Path("/repo/stable_management_repo_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir"),
                "package_pool_dir": Path("/repo/stable_management_repo_dir/foo/bar"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "package_pool_dir": Path("/repo/source_pool_dir/foo/bar"),
                "source_pool_dir": Path("/repo/source_pool_dir"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "package_pool_dir": Path("/default/repo/package_repo_base/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "package_pool_dir": Path("/default/repo/source_repo_base/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir/"),
                "source_pool_dir": Path("/repo/stable_management_repo_dir/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "package_pool_dir": Path("/repo/package_pool_dir/"),
                "source_pool_dir": Path("/repo/package_pool_dir/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "source_pool_dir": Path("/default/repo/package_repo_base/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/other"),
                "source_pool_dir": Path("/default/repo/source_repo_base/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/stable_management_repo_dir/foo/bar/"),
                "stable_management_repo_dir": Path("/repo/stable_management_repo_dir/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/staging_repo_dir/foo/bar/"),
                "staging_repo_dir": Path("/repo/staging_repo_dir/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/testing_repo_dir/foo/bar/"),
                "testing_repo_dir": Path("/repo/testing_repo_dir/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_management_repo_dir": Path("/stable_management_repo_dir/"),
                "stable_repo_dir": Path("/repo/stable/"),
                "staging_repo_dir": Path("/stable_management_repo_dir/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/stable/"),
                "staging_repo_dir": Path("/repo/stable/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/stable/"),
                "staging_repo_dir": Path("/repo/testing/foo/bar/"),
                "testing_repo_dir": Path("/repo/testing/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_management_repo_dir": Path("/stable_management_repo_dir/"),
                "stable_repo_dir": Path("/repo/stable/"),
                "testing_repo_dir": Path("/stable_management_repo_dir/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/stable/"),
                "testing_repo_dir": Path("/repo/stable/foo/bar/"),
            },
            raises(ValueError),
        ),
        (
            {
                "management_repo_base": Path("/default/management_repo_base/"),
                "package_pool_base": Path("/default/pool/package_pool_base/"),
                "package_repo_base": Path("/default/repo/package_repo_base/"),
                "source_pool_base": Path("/default/pool/source_pool_base/"),
                "source_repo_base": Path("/default/repo/source_repo_base/"),
            },
            {
                "stable_repo_dir": Path("/repo/stable/"),
                "staging_repo_dir": Path("/repo/staging/"),
                "testing_repo_dir": Path("/repo/staging/foo/bar/"),
            },
            raises(ValueError),
        ),
    ],
)
def test_ensure_non_overlapping_repositories(
    packagerepo_in_tmp_path: settings.PackageRepo,
    tmp_path: Path,
    caplog: LogCaptureFixture,
    base_overrides: Dict[str, Path],
    repo_overrides: Dict[str, Path],
    expectation: ContextManager[str],
) -> None:
    caplog.set_level(DEBUG)

    _management_repo_base = base_overrides.get("management_repo_base")
    _package_pool_base = base_overrides.get("package_pool_base")
    _package_repo_base = base_overrides.get("package_repo_base")
    _source_pool_base = base_overrides.get("source_pool_base")
    _source_repo_base = base_overrides.get("source_repo_base")

    packagerepo2 = deepcopy(packagerepo_in_tmp_path)

    if repo_overrides.get("stable_management_repo_dir"):
        packagerepo2._stable_management_repo_dir = repo_overrides.get(  # type: ignore[assignment]
            "stable_management_repo_dir"
        )

    if repo_overrides.get("staging_management_repo_dir"):
        packagerepo2._staging_management_repo_dir = repo_overrides.get(  # type: ignore[assignment]
            "staging_management_repo_dir"
        )

    if repo_overrides.get("testing_management_repo_dir"):
        packagerepo2._testing_management_repo_dir = repo_overrides.get(  # type: ignore[assignment]
            "testing_management_repo_dir"
        )

    if repo_overrides.get("package_pool_dir"):
        packagerepo2._package_pool_dir = repo_overrides.get("package_pool_dir")  # type: ignore[assignment]

    if repo_overrides.get("source_pool_dir"):
        packagerepo2._source_pool_dir = repo_overrides.get("source_pool_dir")  # type: ignore[assignment]

    if repo_overrides.get("stable_repo_dir"):
        packagerepo2._stable_repo_dir = repo_overrides.get("stable_repo_dir")  # type: ignore[assignment]

    if repo_overrides.get("staging_repo_dir"):
        packagerepo2._staging_repo_dir = repo_overrides.get("staging_repo_dir")  # type: ignore[assignment]

    if repo_overrides.get("testing_repo_dir"):
        packagerepo2._testing_repo_dir = repo_overrides.get("testing_repo_dir")  # type: ignore[assignment]

    with patch("repod.config.settings.Settings._management_repo_base", _management_repo_base):
        with patch("repod.config.settings.Settings._package_pool_base", _package_pool_base):
            with patch("repod.config.settings.Settings._package_repo_base", _package_repo_base):
                with patch("repod.config.settings.Settings._source_pool_base", _source_pool_base):
                    with patch("repod.config.settings.Settings._source_repo_base", _source_repo_base):
                        with expectation:
                            settings.Settings.ensure_non_overlapping_repositories(
                                repositories=[packagerepo_in_tmp_path, packagerepo2]
                            )


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
                assert isinstance(
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
                assert isinstance(settings.get_default_packagerepo(settings_type=settings_type), settings.PackageRepo)


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
        (Path("/bar/foo"), "foo", Path("/bar"), "bar", raises(ValueError)),
    ],
)
def test_raise_on_path_in_other(
    path: Path, path_name: str, other: Path, other_name: str, expectation: ContextManager[str]
) -> None:
    with expectation:
        settings.raise_on_path_in_other(path=path, path_name=path_name, other=other, other_name=other_name)


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
        assert settings.to_absolute_path(path=path, base_path=base_path) == output


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
def test_settings_get_repo_database_compression(
    has_repo: bool,
    has_namesake_repo: bool,
    reuse_first_repo_name: bool,
    architecture: Optional[ArchitectureEnum],
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
        compression = usersettings.get_repo_database_compression(name=name, architecture=architecture)
        if has_namesake_repo and reuse_first_repo_name and architecture == ArchitectureEnum.ARM:
            assert compression == usersettings.repositories[1].database_compression
        else:
            assert compression == usersettings.repositories[0].database_compression


@mark.parametrize(
    (
        "repo_type, has_repo, has_namesake_repo, name_exists, architecture_exists, debug_exists, staging_exists, "
        "testing_exists, debug, staging, testing, expectation"
    ),
    [
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, True, True, False, False, False, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, True, True, True, False, False, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, True, True, False, True, False, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, True, True, False, False, True, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, False, True, True, True, False, False, False, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, False, True, True, True, True, False, False, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, False, True, True, True, False, True, False, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, False, True, False, True, True, True, False, False, True, does_not_raise()),
        (RepoTypeEnum.MANAGEMENT, True, True, True, False, True, True, True, False, False, False, raises(RuntimeError)),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, False, True, True, True, False, False, raises(RuntimeError)),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, False, True, False, True, False, raises(RuntimeError)),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, True, False, False, False, True, raises(RuntimeError)),
        (
            RepoTypeEnum.MANAGEMENT,
            True,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            raises(RuntimeError),
        ),
        (RepoTypeEnum.MANAGEMENT, True, False, True, True, True, True, True, False, True, True, raises(RuntimeError)),
        (
            RepoTypeEnum.MANAGEMENT,
            False,
            False,
            False,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            raises(RuntimeError),
        ),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, True, True, False, False, False, does_not_raise()),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, True, True, True, False, False, does_not_raise()),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, True, True, False, True, False, does_not_raise()),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, True, True, False, False, True, does_not_raise()),
        (RepoTypeEnum.PACKAGE, True, False, True, True, False, True, True, True, False, False, raises(RuntimeError)),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, False, True, False, True, False, raises(RuntimeError)),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, True, False, False, False, True, raises(RuntimeError)),
        (RepoTypeEnum.PACKAGE, True, False, False, True, True, True, True, False, False, False, raises(RuntimeError)),
        (RepoTypeEnum.PACKAGE, True, False, True, True, True, True, True, False, True, True, raises(RuntimeError)),
        (
            RepoTypeEnum.PACKAGE,
            False,
            False,
            False,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            raises(RuntimeError),
        ),
        (RepoTypeEnum.POOL, True, False, True, True, False, False, False, False, False, False, does_not_raise()),
        (RepoTypeEnum.POOL, True, False, True, True, False, False, False, True, False, False, does_not_raise()),
        (RepoTypeEnum.POOL, True, False, True, True, False, False, False, False, True, False, does_not_raise()),
        (RepoTypeEnum.POOL, True, False, True, True, False, False, False, False, False, True, does_not_raise()),
        (None, True, False, True, True, True, True, True, False, False, False, raises(RuntimeError)),
    ],
)
def test_settings_get_repo_path(
    usersettings: settings.UserSettings,
    repo_type: RepoTypeEnum,
    has_repo: bool,
    has_namesake_repo: bool,
    name_exists: bool,
    architecture_exists: bool,
    debug_exists: bool,
    staging_exists: bool,
    testing_exists: bool,
    debug: bool,
    staging: bool,
    testing: bool,
    expectation: ContextManager[str],
) -> None:
    name = Path("foo")
    architecture = None

    if name_exists:
        name = usersettings.repositories[0].name

    if architecture_exists:
        architecture = usersettings.repositories[0].architecture

    if not debug_exists:
        usersettings.repositories[0].debug = None

    if not staging_exists:
        usersettings.repositories[0].staging = None

    if not testing_exists:
        usersettings.repositories[0].testing = None

    if not has_repo:
        usersettings.repositories = []
    else:
        if has_namesake_repo:
            namesake = deepcopy(usersettings.repositories[0])
            namesake.architecture = ArchitectureEnum.ARM
            usersettings.repositories.append(namesake)

    with expectation:
        path = usersettings.get_repo_path(
            repo_type=repo_type, name=name, architecture=architecture, debug=debug, staging=staging, testing=testing
        )

        match repo_type, debug, staging, testing:
            case RepoTypeEnum.MANAGEMENT, True, False, False:
                assert path == usersettings.repositories[0]._debug_management_repo_dir
            case RepoTypeEnum.MANAGEMENT, False, True, False:
                assert path == usersettings.repositories[0]._staging_management_repo_dir
            case RepoTypeEnum.MANAGEMENT, False, False, True:
                assert path == usersettings.repositories[0]._testing_management_repo_dir
            case RepoTypeEnum.MANAGEMENT, False, False, False:
                assert path == usersettings.repositories[0]._stable_management_repo_dir
            case RepoTypeEnum.PACKAGE, True, False, False:
                assert path == usersettings.repositories[0]._debug_repo_dir
            case RepoTypeEnum.PACKAGE, False, True, False:
                assert path == usersettings.repositories[0]._staging_repo_dir
            case RepoTypeEnum.PACKAGE, False, False, True:
                assert path == usersettings.repositories[0]._testing_repo_dir
            case RepoTypeEnum.PACKAGE, False, False, False:
                assert path == usersettings.repositories[0]._stable_repo_dir
            case RepoTypeEnum.POOL, False, False, False:
                assert path == usersettings.repositories[0]._package_pool_dir
