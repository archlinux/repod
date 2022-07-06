from pathlib import Path

from xdg.BaseDirectory import xdg_config_home, xdg_state_home

from repod.common.enums import CompressionTypeEnum, SettingsTypeEnum

DEFAULT_DATABASE_COMPRESSION = CompressionTypeEnum.GZIP
SETTINGS_LOCATION = {
    SettingsTypeEnum.SYSTEM: Path("/etc/repod.conf"),
    SettingsTypeEnum.USER: Path(xdg_config_home + "/repod/repod.conf"),
}
SETTINGS_OVERRIDE_LOCATION = {
    SettingsTypeEnum.SYSTEM: Path("/etc/repod.conf.d/"),
    SettingsTypeEnum.USER: Path(xdg_config_home + "/repod/repod.conf.d/"),
}
PACKAGE_REPO_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/repo"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/repo/"),
}
SOURCE_REPO_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/source"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/source/"),
}

MANAGEMENT_REPO = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/management/default/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/management/default/"),
}
PACKAGE_POOL_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/pool/package/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/pool/package/"),
}
SOURCE_POOL_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/pool/source/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/source/package/"),
}
