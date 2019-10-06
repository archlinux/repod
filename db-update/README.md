# db-update

To test:

1. Run `./demo-init.sh` to create `staging` and `meta` folders structure (for `*.pkg.tar.xz` and json files respectively)
1. Copy a few packages (with signatures) to e.g. `staging/community` dir
1. Run `./db-update/`
1. Check the contents of `meta/**/*.json` files!
