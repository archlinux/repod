# Getting Started

This guide aims to get you started developing on arch-repo-management.<br>
It requires some basic understanding of Arch, packages and mirrors.<br>
<br>
First thing you will need is db-files to test against.<br>
We can use the pacman database cache stored in `/var/lib/pacman/sync/` for this purpose.

## Copying pacman databases

```bash
$ sudo pacman -Fy
$ TEST_DIR="$HOME/dev-repo-management/"
$ mkdir -p "$TEST_DIR"
$ cp -av /var/lib/pacman/sync/*.{db,files} "$TEST_DIR/"
```

## Populate json structure

We'll use this projects tool `db2json` to create a JSON state of the above database files.<br>
Note that examples only executes on `core`. Run the same command on the other repositories `.db`/`.files` databases in `$TEST_DIR` if needed.

```bash
$ poetry run db2json "$TEST_DIR/core.db" "$TEST_DIR/"
```

We are using `poetry` here to avoid having to install `arch-repo-management` which in turn creates `/usr/bin/db2json` normally.