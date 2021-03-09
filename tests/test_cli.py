from argparse import Namespace

from mock import Mock, patch

from repo_management import cli


@patch("repo_management.operations.dump_db_to_json_files")
@patch("repo_management.argparse.ArgParseFactory")
def test_db2json(argparsefactory_mock: Mock, dump_db_to_json_files_mock: Mock) -> None:
    namespace = Namespace(db_file="db_file", output_dir="output_dir")
    argparsefactory_mock.db2json.return_value = Mock(parse_args=Mock(return_value=namespace))
    cli.db2json()
    dump_db_to_json_files_mock.assert_called_once_with(input_path=namespace.db_file, output_path=namespace.output_dir)
