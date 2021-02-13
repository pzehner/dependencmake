import logging
import sys
from argparse import ArgumentParser, Namespace

from path import Path

from dependen6make.config import get_config, check_config
from dependen6make.dependency_list import DependencyList
from dependen6make.exceptions import Dependen6makeError


logger = logging.getLogger(__name__)


def get_parser() -> ArgumentParser:
    """Create a parser."""
    parser = ArgumentParser(
        prog="dependen6make", description="Dependence manager for projects using CMake"
    )
    subparsers = parser.add_subparsers()

    # list parser
    list_parser = subparsers.add_parser("list", help="list dependencies")
    list_parser.set_defaults(function=run_list)

    # fetch parser
    fetch_parser = subparsers.add_parser("fetch", help="fetch dependencies")
    fetch_parser.set_defaults(function=run_fetch)

    # add path to source last
    parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )

    return parser


def run_list(args: Namespace, output=sys.stdout):
    """Run the list command."""
    config = get_config(args.path)
    check_config(config)

    dependency_list = DependencyList()
    dependency_list.create_dependencies(config["dependencies"])
    dependency_list.describe(output)


def run_fetch(args: Namespace, output=sys.stdout):
    """Run the fetch command."""
    config = get_config(args.path)
    check_config(config)

    dependency_list = DependencyList()
    dependency_list.create_dependencies(config["dependencies"])
    dependency_list.fetch(output)


def main():
    parser = get_parser()
    args = parser.parse_args()

    try:
        args.function(args)

    except Dependen6makeError as error:
        logger.critical(error)
        exit(1)


if __name__ == "__main__":
    main()
