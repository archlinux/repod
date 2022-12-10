"""Tests for repod.cli.argparse."""
from contextlib import nullcontext as does_not_raise
from typing import ContextManager
from unittest.mock import Mock, patch

from pydantic import AnyUrl
from pydantic.tools import parse_obj_as
from pytest import mark, raises

from repod.cli import argparse


def test_argparsefactory__init__() -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.__init__."""
    assert isinstance(argparse.ArgParseFactory().parser, argparse.ArgumentParser)  # nosec: B101


def test_argparsefactory_repod_file() -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.repod_file."""
    assert isinstance(argparse.ArgParseFactory().repod_file(), argparse.ArgumentParser)  # nosec: B101


def test_sphinx_repod_file() -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.sphinx_repod_file."""
    assert isinstance(argparse.sphinx_repod_file(), argparse.ArgumentParser)  # nosec: B101


@patch(
    "repod.cli.argparse.Path",
    Mock(return_value=Mock(exists=Mock(side_effect=[False, True, True]), is_file=Mock(side_effect=[False, True]))),
)
def test_argparsefactory_string_to_file_path() -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.string_to_file_path."""
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_file_path("foo")
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_file_path("foo")
    assert argparse.ArgParseFactory.string_to_file_path("foo")  # nosec: B101


@patch(
    "os.access",
    Mock(side_effect=[False, False, True, True]),
)
@patch("repod.cli.argparse.Path.exists", Mock(side_effect=[True, True, False, False, False, True, False]))
@patch("repod.cli.argparse.Path.is_file", Mock(side_effect=[False, True, True]))
@patch("repod.cli.argparse.Path.parent", return_value=Mock())
def test_argparsefactory_string_to_writable_file_path(parent_mock: Mock) -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.string_to_writable_file_path."""
    parent_mock.exists.side_effect = [False, True, True, True]
    parent_mock.is_dir.side_effect = [False, True, True]
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_writable_file_path("foo")
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_writable_file_path("foo")
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_writable_file_path("foo")
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_writable_file_path("foo")
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_writable_file_path("foo")
    assert argparse.ArgParseFactory.string_to_writable_file_path("foo")  # nosec: B101
    assert argparse.ArgParseFactory.string_to_writable_file_path("foo")  # nosec: B101


@patch(
    "repod.cli.argparse.Path",
    Mock(return_value=Mock(exists=Mock(side_effect=[False, True, True]), is_dir=Mock(side_effect=[False, True]))),
)
def test_argparsefactory_string_to_dir_path() -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.string_to_dir_path."""
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_dir_path("foo")
    with raises(argparse.ArgumentTypeError):
        argparse.ArgParseFactory.string_to_dir_path("foo")
    assert argparse.ArgParseFactory.string_to_dir_path("foo")  # nosec: B101


@mark.parametrize(
    "input_string, expectation, return_value",
    [
        ("foo=https://foobar.com", does_not_raise(), ("foo", parse_obj_as(AnyUrl, "https://foobar.com"))),
        ("foo = https://foobar.com", does_not_raise(), ("foo", parse_obj_as(AnyUrl, "https://foobar.com"))),
        ("foo", raises(argparse.ArgumentTypeError), None),
        ("foo bar = https://foobar.com", raises(argparse.ArgumentTypeError), None),
        ("foo=https://foobar.com beh", raises(argparse.ArgumentTypeError), None),
    ],
)
def test_argparsefactory_string_to_tuple(
    input_string: str,
    expectation: ContextManager[str],
    return_value: tuple[str, AnyUrl],
) -> None:
    """Tests for repod.cli.argparse.ArgParseFactory.string_to_tuple."""
    with expectation:
        assert argparse.ArgParseFactory.string_to_tuple(input_=input_string) == return_value  # nosec: B101
