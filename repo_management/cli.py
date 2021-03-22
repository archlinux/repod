from argparse import ArgumentTypeError
from sys import exit

from repo_management import argparse, defaults, errors, operations


def db2json() -> None:
    """The entry point for the db2json script

    The method calls operations.dump_db_to_json_files() which creates JSON files for each member of a provided
    repository database file.
    """

    try:
        args = argparse.ArgParseFactory.db2json().parse_args()
        operations.dump_db_to_json_files(
            input_path=args.db_file,
            output_path=args.output_dir,
        )
    except (errors.RepoManagementError, ArgumentTypeError) as e:
        print(e)
        exit(1)


def json2db() -> None:
    """The entry point for the json2db script

    The method calls operations.create_db_from_json_files() which creates a repository database from a set of JSON files
    in a directory.
    """

    try:
        args = argparse.ArgParseFactory.json2db().parse_args()
        operations.create_db_from_json_files(
            input_path=args.input_dir,
            output_path=args.db_file,
            db_type=defaults.RepoDbType.FILES if args.files else defaults.RepoDbType.DEFAULT,
        )
    except (errors.RepoManagementError, ArgumentTypeError) as e:
        print(e)
        exit(1)
