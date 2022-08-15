from pathlib import Path

from xdg.BaseDirectory import xdg_config_home, xdg_state_home

from repod.common.enums import ArchitectureEnum, CompressionTypeEnum, SettingsTypeEnum

DEFAULT_ARCHITECTURE = ArchitectureEnum.ANY
DEFAULT_DATABASE_COMPRESSION = CompressionTypeEnum.GZIP
DEFAULT_NAME = "default"

SETTINGS_LOCATION = {
    SettingsTypeEnum.SYSTEM: Path("/etc/repod.conf"),
    SettingsTypeEnum.USER: Path(xdg_config_home + "/repod/repod.conf"),
}
SETTINGS_OVERRIDE_LOCATION = {
    SettingsTypeEnum.SYSTEM: Path("/etc/repod.conf.d/"),
    SettingsTypeEnum.USER: Path(xdg_config_home + "/repod/repod.conf.d/"),
}

MANAGEMENT_REPO_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/management/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/management/"),
}
PACKAGE_POOL_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/data/pool/package/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/data/pool/package/"),
}
PACKAGE_REPO_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/data/repo/package/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/data/repo/package/"),
}
SOURCE_POOL_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/data/pool/source/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/data/pool/source/"),
}
SOURCE_REPO_BASE = {
    SettingsTypeEnum.SYSTEM: Path("/var/lib/repod/data/repo/source/"),
    SettingsTypeEnum.USER: Path(xdg_state_home + "/repod/data/repo/source/"),
}
