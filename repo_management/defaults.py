# mapping of sections of pkgbase desc file <-> JSON key
DESC_JSON = {
    "%BASE%": "base",
    "%VERSION%": "version",
    "%MAKEDEPENDS%": "makedepends",
    "%CHECKDEPENDS%": "checkdepends",
    "%FILENAME%": "filename",
    "%NAME%": "name",
    "%DESC%": "desc",
    "%GROUPS%": "groups",
    "%CSIZE%": "csize",
    "%ISIZE%": "isize",
    "%MD5SUM%": "md5sum",
    "%SHA256SUM%": "sha256sum",
    "%PGPSIG%": "pgpsig",
    "%URL%": "url",
    "%LICENSE%": "licenses",
    "%ARCH%": "arch",
    "%BUILDDATE%": "builddate",
    "%PACKAGER%": "packager",
    "%REPLACES%": "replaces",
    "%CONFLICTS%": "conflicts",
    "%PROVIDES%": "provides",
    "%DEPENDS%": "depends",
    "%OPTDEPENDS%": "optdepends",
    "%BACKUP%": "backup",
}

FILES_JSON = {"%FILES%": "files"}
