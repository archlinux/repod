destdir := ""

build:
  python -m build --wheel --no-isolation
  python -c 'from repod import export_schemas; from pathlib import Path; export_schemas(Path("docs/schema/"))'
  PYTHONPATH="$PWD" sphinx-build -M man docs/ docs/_build

check:
  python -m pytest -vv -k 'not (integration or regex)'

install:
  test -z {{destdir}} && python -m installer dist/*.whl
  test -n {{destdir}} && python -m installer --destdir="{{destdir}}" dist/*.whl
  install -vDm 644 docs/_build/man/man1/*.1 -t "{{destdir}}/usr/share/man/man1/"
  install -vDm 644 docs/_build/man/man5/*.5 -t "{{destdir}}/usr/share/man/man5/"
  install -vdm 755 "{{destdir}}/etc/repod.conf.d/"
  install -vdm 755 "{{destdir}}/var/lib/repod/management/"
  install -vdm 755 "{{destdir}}/var/lib/repod/data/pool/package/"
  install -vdm 755 "{{destdir}}/var/lib/repod/data/pool/source/"
  install -vdm 755 "{{destdir}}/var/lib/repod/data/repo/package/"
  install -vdm 755 "{{destdir}}/var/lib/repod/data/repo/source/"
