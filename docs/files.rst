=====
Files
=====

The files repository sync databases contain per-package ``files`` files, that
carry identifiers and their values, which serve to describe the contents of a
package.

Identifiers are composed of a string in all capital letters ``[A-Z]`` with a
leading and a trailing ``%`` character.
All identifiers as well as values are provided on a per-line basis in a
``files`` file, leaving an empty line between each identifier/value pair.

Identifiers may be required or optional. As requirements change over time and
identifiers and their values may be added or removed, the ``files`` files are
distinguished using the below versioning.


Files v1
--------

* ``%FILES%`` (**required**): A list of files and directories contained in a
  package (one file per line below the identifier)
