from repo_management import argparse, operations


def db2json() -> None:
    """The entry point for the db2json script

    The method calls operations.dump_db_to_json_files() which creates JSON files for each member of a provided
    repository database file.
    """

    args = argparse.ArgParseFactory.db2json().parse_args()
    operations.dump_db_to_json_files(
        input_path=args.db_file,
        output_path=args.output_dir,
    )
