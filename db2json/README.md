Converts a pacman database into several JSON files, named after pkgbase. If
pkgbase is not available, fall back to pkgname.

Read `foo.db` and write the files to a given directory:

  $ python3 db2json.py <foo.db> <path/to/dir>
