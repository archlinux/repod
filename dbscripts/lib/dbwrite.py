import io
import tarfile


def writefield(out: io.StringIO, name: str, field):
    if field is None:
        pass
    elif not isinstance(field, list):
        print(f"%{name}%", field, sep="\n", end="\n\n", file=out)
    elif field:
        print(f"%{name}%", *field, sep="\n", end="\n\n", file=out)


def descfile(base: str, version: str, data) -> bytes:
    out = io.StringIO()

    writefield(out, "FILENAME", data["filename"])
    writefield(out, "NAME", data["name"])
    writefield(out, "BASE", base)
    writefield(out, "VERSION", version)
    writefield(out, "DESC", data.get("desc"))
    writefield(out, "GROUPS", data.get("groups"))
    writefield(out, "CSIZE", data.get("csize"))
    writefield(out, "ISIZE", data.get("isize"))

    # add checksums
    writefield(out, "MD5SUM", data.get("md5sum"))
    writefield(out, "SHA256SUM", data.get("sha256sum"))

    # add PGP sig
    writefield(out, "PGPSIG", data.get("pgpsig"))

    writefield(out, "URL", data.get("url"))
    writefield(out, "LICENSE", data.get("license"))
    writefield(out, "ARCH", data.get("arch"))
    writefield(out, "BUILDDATE", data.get("builddate"))
    writefield(out, "PACKAGER", data.get("packager"))
    writefield(out, "REPLACES", data.get("replaces"))
    writefield(out, "CONFLICTS", data.get("conflicts"))
    writefield(out, "PROVIDES", data.get("provides"))

    writefield(out, "DEPENDS", data.get("depends"))
    writefield(out, "OPTDEPENDS", data.get("optdepends"))
    writefield(out, "MAKEDEPENDS", data.get("makedepends"))
    writefield(out, "CHECKDEPENDS", data.get("checkdepends"))

    return out.getvalue().encode()


def generate_dbs(meta):
    for repo, pkgbases in meta.items():
        with tarfile.open(f"{repo}.db.tar.gz", mode="w:gz") as tf:
            for pkgbase, pkginfo in pkgbases.items():
                version = pkginfo["version"]
                for package in pkginfo["packages"]:
                    name = package["name"]
                    dirname = f"{name}-{version}"

                    entry = tarfile.TarInfo(dirname)
                    entry.type = tarfile.DIRTYPE
                    tf.addfile(entry)

                    dfile = descfile(pkgbase, version, package)
                    entry = tarfile.TarInfo(f"{dirname}/desc")
                    entry.size = len(dfile)
                    tf.addfile(entry, io.BytesIO(dfile))
