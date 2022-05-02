Binary repository
_________________

The git repository layout directly reflects the binary repository layout. This
means, that the location of a *package*'s git repository in its specific
location needs to match its built package in the respective binary repository.

If *package_a* in version *1:2-3* is in::

  x86_64
    core
      package_a

its binary package will be symlinked from the pool to the respective location::

  .
  ├── /srv/ftp/core
  │   └── os
  │       └── x86_64
  │           ├── core.db
  │           ├── [..]
  │           ├── package_a-1:2-3-x86_64.pkg.tar.xz -> ../../../pool/package_a-1:2-3-x86_64.pkg.tar.xz
  │           ├── package_a-1:2-3-x86_64.pkg.tar.xz.sig -> ../../../pool/package_a-1:2-3-x86_64.pkg.tar.xz.sig
  │           └── [..]
  └── /srv/ftp/pool
      ├── [..]
      ├── package_a-1:2-3-x86_64.pkg.tar.xz
      ├── package_a-1:2-3-x86_64.pkg.tar.xz.sig
      └── [..]
