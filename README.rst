arch-repo-management
####################

This is a PoC for a modular, Python based tool, that can manage git based
repositories (the details are explained below) and their respective binary
repository counterparts. The two not necessarily have to be located on the same
host.

The below implementational details need to be mocked and tested against each
other.

Previous discussion: https://conf.archlinux.org/reports/archconf_2019/

.. _git-subtree: https://man.archlinux.org/man/git/git-subtree.1.en
.. _git-read-tree: https://man.archlinux.org/man/git/git-read-tree.1.en
.. _git-submodule: https://man.archlinux.org/man/git/git-submodule.1.en
.. _.gitmodules: https://man.archlinux.org/man/git/gitmodules.5.en
.. _git-mv: https://man.archlinux.org/man/git/git-mv.1.en
.. _git-log: https://man.archlinux.org/man/git/git-log.1.en
.. _architecture: https://man.archlinux.org/man/pacman/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES

