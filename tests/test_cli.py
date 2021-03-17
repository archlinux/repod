from argparse import Namespace

from mock import Mock, patch
from pytest import mark

from repo_management import cli, defaults


@patch("repo_management.operations.dump_db_to_json_files")
@patch("repo_management.argparse.ArgParseFactory")
def test_db2json(argparsefactory_mock: Mock, dump_db_to_json_files_mock: Mock) -> None:
    namespace = Namespace(db_file="db_file", output_dir="output_dir")
    argparsefactory_mock.db2json.return_value = Mock(parse_args=Mock(return_value=namespace))
    cli.db2json()
    dump_db_to_json_files_mock.assert_called_once_with(input_path=namespace.db_file, output_path=namespace.output_dir)


@mark.parametrize("files, db_type", [(True, defaults.RepoDbType.FILES), (False, defaults.RepoDbType.DEFAULT)])
@patch("repo_management.operations.create_db_from_json_files")
@patch("repo_management.argparse.ArgParseFactory")
def test_json2db(
    argparsefactory_mock: Mock, create_db_from_json_files: Mock, files: bool, db_type: defaults.RepoDbType
) -> None:
    namespace = Namespace(db_file="db_file", input_dir="input_dir", files=files)
    argparsefactory_mock.json2db.return_value = Mock(parse_args=Mock(return_value=namespace))
    cli.json2db()
    create_db_from_json_files.assert_called_once_with(
        input_path=namespace.input_dir,
        output_path=namespace.db_file,
        db_type=db_type,
    )
