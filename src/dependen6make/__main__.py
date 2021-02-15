import logging
import sys
from argparse import ArgumentParser, Namespace

from path import Path

from dependen6make.cmake import CMAKE_PREFIX_PATH
from dependen6make.config import get_config, check_config, CONFIG_NAME, create_config
from dependen6make.dependency_list import DependencyList
from dependen6make.exceptions import Dependen6makeError
from dependen6make.filesystem import CACHE_INSTALL


logger = logging.getLogger(__name__)


def get_parser() -> ArgumentParser:
    """Create a parser."""
    parser = ArgumentParser(
        prog="dependen6make", description="Dependence manager for projects using CMake"
    )
    subparsers = parser.add_subparsers()

    # create config parser
    create_config_parser = subparsers.add_parser(
        "create-config", help="create a new configuration file"
    )
    create_config_parser.set_defaults(function=run_create_config)
    create_config_parser.add_argument(
        "-f", "--force", action="store_true", help="overwrite any existing config file"
    )

    # list parser
    list_parser = subparsers.add_parser("list", help="list dependencies")
    list_parser.set_defaults(function=run_list)

    # fetch parser
    fetch_parser = subparsers.add_parser("fetch", help="fetch dependencies")
    fetch_parser.set_defaults(function=run_fetch)

    # build parser
    build_parser = subparsers.add_parser("build", help="fetch and build dependencies")
    build_parser.set_defaults(function=run_build)

    # install parser
    install_parser = subparsers.add_parser(
        "install", help="fetch, build and install dependencies"
    )
    install_parser.set_defaults(function=run_install)

    # add path to source last
    parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )

    return parser


def run_create_config(args: Namespace, output=sys.stdout):
    """Run the create-config command."""
    create_config(args.force)

    output.write(f"Config file created in {CONFIG_NAME}\n")


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

    output.write("Done\n")


def run_build(args: Namespace, output=sys.stdout):
    """Run the build command."""
    config = get_config(args.path)
    check_config(config)

    dependency_list = DependencyList()
    dependency_list.create_dependencies(config["dependencies"])
    dependency_list.fetch(output)
    dependency_list.build(output)

    output.write("Done\n")


def run_install(args: Namespace, output=sys.stdout):
    """Run the install command."""
    config = get_config(args.path)
    check_config(config)

    dependency_list = DependencyList()
    dependency_list.create_dependencies(config["dependencies"])
    dependency_list.fetch(output)
    dependency_list.build(output)
    dependency_list.install(output)

    output.write("Done\n\n")

    output.write(f"You can call CMake with {CMAKE_PREFIX_PATH.format(CACHE_INSTALL)}\n")


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
