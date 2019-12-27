#!/usr/bin/env python3
# db2json - convert a foo.db.tar.gz into JSON

import io
import json
import sys
import tarfile
import warnings


def main():
    # tarfile supports symbolic links, so the .db can be taken directly
    db_path = sys.argv[1]
    json_dir = sys.argv[2]

    # mapping db section <-> JSON key
    keys = {
        '%BASE%': 'base',
        '%VERSION%': 'version',
        '%MAKEDEPENDS%': 'makedepends',
        '%CHECKDEPENDS%': 'checkdepends',
        '%FILENAME%': 'filename',
        '%NAME%': 'name',
        '%DESC%': 'desc',
        '%GROUPS%': 'groups',
        '%CSIZE%': 'csize',
        '%ISIZE%': 'isize',
        '%MD5SUM%': 'md5sum',
        '%SHA256SUM%': 'sha256sum',
        '%PGPSIG%': 'pgpsig',
        '%URL%': 'url',
        '%LICENSE%': 'licenses',
        '%ARCH%': 'arch',
        '%BUILDDATE%': 'builddate',
        '%PACKAGER%': 'packager',
        '%REPLACES%': 'replaces',
        '%CONFLICTS%': 'conflicts',
        '%PROVIDES%': 'provides',
        '%DEPENDS%': 'depends',
        '%OPTDEPENDS%': 'optdepends',
        '%BACKUP%': 'backup',
        '%FILES%': 'files'
    }

    # arch databases are always gzip
    with tarfile.open(db_path, "r:gz") as db:
        # as split packages for the same pkgbase may appear anywhere in the database,
        # load them in memory and later write the merged structures to disk.
        # warning: uses 400mb RES on community.files (~220mb uncompressed)
        # (alternative: write and update intermediary results to disk)
        base_dict = {}

        # files (list of strings)
        files = []
        json_name = None

        # 'files' may or may not appear before 'desc' in the tar archive; use a marker
        # to indicate when it is encountered.
        db_file_processed = None

        while True:
            curr = db.next()
            # end of archive
            if curr is None:
                break

            # process directory foo/{files,desc} only
            if curr.isdir():
                # reset markers
                db_file_processed = None
                json_name = None

                # reset files list
                files = []
                continue

            # set up reading db entry
            data = db.extractfile(curr).read()
            data_io = io.BytesIO(data)

            # check if we are in a files section
            db_file = curr.name.split('/')[1]

            if db_file == 'files':
                for line in data_io.readlines():
                    rec = line.decode('utf-8').rstrip()

                    if rec == '%FILES%':
                        continue  # skip header
                    else:
                        files.append(rec)

                if db_file_processed == 'desc':
                    if json_name is None:
                        raise ValueError(db_file[0] + ": files: pkgbase is undefined")

                    # add files list to matching (last appended) split package
                    base_dict[json_name]['packages'][-1]['files'] = files

                # done processing 'files', continue to next entry
                db_file_processed = 'files'
                continue

            elif db_file == 'desc':
                pass  # begin processing of desc file below
            else:
                raise ValueError(db_file + ": unknown file in database")

            # marker for reading sections with multiple entries
            in_section = None

            # empty JSON structure (base)
            base = {}
            package = {}

            for line in data_io.readlines():
                # metadata fields may contain UTF-8
                rec = line.decode('utf-8').rstrip()

                if rec == str():
                    in_section = None
                    continue

                # we have entered a new section
                elif in_section is None and rec in keys:
                    in_section = rec
                    continue
                elif in_section is None:
                    raise ValueError("Unknown section " + rec + " in database")

                # base.json
                if in_section == '%BASE%':
                    json_name = rec

                # global metadata
                elif in_section == '%VERSION%':
                    base['version'] = rec

                elif in_section == '%MAKEDEPENDS%' or in_section == '%CHECKDEPENDS%':
                    key = keys[in_section]

                    if key in base:
                        base[key].append(rec)
                    else:
                        base[key] = [rec]

                # split metadata (packages), strings
                elif (in_section == '%FILENAME%'
                        or in_section == '%NAME%'
                        or in_section == '%DESC%'
                        or in_section == '%MD5SUM%'
                        or in_section == '%SHA256SUM%'
                        or in_section == '%PGPSIG%'
                        or in_section == '%URL%'
                        or in_section == '%ARCH%'
                        or in_section == '%PACKAGER%'
                ):
                    key = keys[in_section]
                    package[key] = rec

                # split metadata (packages), integers
                elif (in_section == '%CSIZE%'
                        or in_section == '%ISIZE%'
                        or in_section == '%BUILDDATE%'
                ):
                    key = keys[in_section]
                    package[key] = int(rec)

                # split metadata (packages), lists
                elif (in_section == '%GROUPS%'
                        or in_section == '%LICENSE%'
                        or in_section == '%REPLACES%'
                        or in_section == '%CONFLICTS%'
                        or in_section == '%PROVIDES%'
                        or in_section == '%DEPENDS%'
                        or in_section == '%OPTDEPENDS%'
                        or in_section == '%BACKUP%'
                ):
                    key = keys[in_section]
                    if key in package:
                        package[key].append(rec)
                    else:
                        package[key] = [rec]

            # desc for very old packages may not contain %BASE%
            if json_name is None:
                pkgname = package['name']
                warnings.warn(pkgname + ": %BASE% not set in database")

                # fall back to pkgname.json
                json_name = pkgname

            # append contents of 'files' if seen before 'desc'
            if db_file_processed == 'files':
                if len(files) == 0:
                    raise ValueError(json_name + ': empty list of files')

                package['files'] = files

            # append package to matching pkgbase
            if json_name in base_dict:
                # check that global fields are unchanged (transitive)
                if base_dict[json_name]['version'] != base['version']:
                    warnings.warn("split pkgver does not match pkgbase: " + package['name'])

                # append split package information
                base_dict[json_name]['packages'].append(package)
            else:
                # add first split package of pkgbase
                base['packages'] = [package]
                base_dict[json_name] = base

            # done processing desc file
            db_file_processed = 'desc'

        # write json for pkgbase
        for pb in base_dict.keys():
            with open(json_dir + "/" + pb + ".json", "w") as j:
                json.dump(base_dict[pb], j, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()
