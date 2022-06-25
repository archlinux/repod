from pathlib import Path

SETTINGS_LOCATION = Path("/etc/repod.conf")
SETTINGS_OVERRIDE_LOCATION = Path("/etc/repod.conf.d/")
PACKAGE_REPO_BASE = Path("/var/lib/repod/repo")
SOURCE_REPO_BASE = Path("/var/lib/repod/source")

MANAGEMENT_REPO = Path("/var/lib/repod/management/default")
PACKAGE_POOL = Path("/var/lib/repod/pool/package/default")
SOURCE_POOL = Path("/var/lib/repod/pool/source/default")
