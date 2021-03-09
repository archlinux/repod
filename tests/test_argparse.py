import argparse

from mock import Mock, patch
from pytest import raises

from repo_management import argparse as repo_argparse


def test_argparsefactory__init__() -> None:
    assert isinstance(repo_argparse.ArgParseFactory().parser, argparse.ArgumentParser)


def test_argparsefactory__db2json() -> None:
    assert isinstance(repo_argparse.ArgParseFactory.db2json(), argparse.ArgumentParser)


@patch(
    "repo_management.argparse.Path",
    Mock(return_value=Mock(exists=Mock(side_effect=[False, True, True]), is_file=Mock(side_effect=[False, True]))),
)
def test_argparsefactory_string_to_file_path() -> None:
    with raises(argparse.ArgumentTypeError):
        repo_argparse.ArgParseFactory.string_to_file_path("foo")
    with raises(argparse.ArgumentTypeError):
        repo_argparse.ArgParseFactory.string_to_file_path("foo")
    assert repo_argparse.ArgParseFactory.string_to_file_path("foo")


@patch(
    "repo_management.argparse.Path",
    Mock(return_value=Mock(exists=Mock(side_effect=[False, True, True]), is_dir=Mock(side_effect=[False, True]))),
)
def test_argparsefactory_string_to_dir_path() -> None:
    with raises(argparse.ArgumentTypeError):
        repo_argparse.ArgParseFactory.string_to_dir_path("foo")
    with raises(argparse.ArgumentTypeError):
        repo_argparse.ArgParseFactory.string_to_dir_path("foo")
    assert repo_argparse.ArgParseFactory.string_to_dir_path("foo")
