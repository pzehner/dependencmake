import logging
import sys
from argparse import REMAINDER, ArgumentParser, Namespace

from path import Path

from dependencmake.cmake import CMAKE_PREFIX_PATH
from dependencmake.config import CONFIG_NAME, create_config
from dependencmake.dependency_list import DependencyList
from dependencmake.exceptions import DependenCmakeError
from dependencmake.filesystem import CACHE_INSTALL, clean
from dependencmake.version import __version__

logger = logging.getLogger(__name__)


def get_parser() -> ArgumentParser:
    """Create a parser."""
    parser = ArgumentParser(
        prog="dependencmake",
        description="Dependencies manager for projects using CMake.",
    )
    parser.set_defaults(function=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()

    # version command
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # create config parser
    create_config_parser = subparsers.add_parser(
        "create-config", help="create a new configuration file"
    )
    create_config_parser.set_defaults(function=run_create_config)
    create_config_parser.add_argument(
        "-f", "--force", action="store_true", help="overwrite any existing config file"
    )
    create_config_parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )

    # list parser
    list_parser = subparsers.add_parser("list", help="list dependencies")
    list_parser.set_defaults(function=run_list)
    list_parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )

    # fetch parser
    fetch_parser = subparsers.add_parser("fetch", help="fetch dependencies")
    fetch_parser.set_defaults(function=run_fetch)
    fetch_parser.add_argument("-f", "--force", help="clean fetch cache beforehand")
    fetch_parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )

    # build parser
    build_parser = subparsers.add_parser("build", help="fetch and build dependencies")
    build_parser.set_defaults(function=run_build)
    build_parser.add_argument(
        "-f", "--force", help="clean fetch and build caches beforehand"
    )
    build_parser.add_argument(
        "--install-path",
        type=Path,
        help=f"specify install directory, default to {CACHE_INSTALL}",
        metavar="install-prefix",
    )
    build_parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )
    build_parser.add_argument(
        "rest",
        nargs=REMAINDER,
        metavar="cmake-args",
        help="other arguments will be passed to CMake at configure step",
    )

    # install parser
    install_parser = subparsers.add_parser(
        "install", help="fetch, build and install dependencies"
    )
    install_parser.set_defaults(function=run_install)
    install_parser.add_argument(
        "-f", "--force", help="clean fetch, build and install caches beforehand"
    )
    install_parser.add_argument(
        "--install-path",
        type=Path,
        help=f"specify install directory, default to {CACHE_INSTALL}",
        metavar="install-prefix",
    )
    install_parser.add_argument(
        "path",
        type=Path,
        help="explicitly specify a source directory",
        metavar="path-to-source",
    )
    install_parser.add_argument(
        "rest",
        nargs=REMAINDER,
        metavar="cmake-args",
        help="other arguments will be passed to CMake at configure step",
    )

    # clean parser
    clean_parser = subparsers.add_parser(
        "clean",
        help="clean cache",
        description="Clean cache directories. By default, only the build "
        "cache is cleaned.",
    )
    clean_parser.set_defaults(function=run_clean)
    clean_parser.add_argument(
        "-f", "--fetch", action="store_true", help="clean fetch cache"
    )
    clean_parser.add_argument(
        "-b", "--build", action="store_true", help="clean build cache"
    )
    clean_parser.add_argument(
        "-i", "--install", action="store_true", help="clean install cache"
    )
    clean_parser.add_argument(
        "-a", "--all", action="store_true", help="clean all caches"
    )
    clean_parser.add_argument(
        "--install-path",
        type=Path,
        help=f"specify install directory, default to {CACHE_INSTALL}",
        metavar="install-prefix",
    )

    return parser


def run_create_config(args: Namespace, output=sys.stdout):
    """Run the create-config command."""
    create_config(args.path, args.force)

    output.write(f"Config file created in {CONFIG_NAME}\n")


def run_list(args: Namespace, output=sys.stdout):
    """Run the list command."""
    dependency_list = DependencyList()
    dependency_list.create_dependencies(args.path)
    dependency_list.create_subdependencies()
    dependency_list.describe(output)


def run_fetch(args: Namespace, output=sys.stdout):
    """Run the fetch command."""
    if args.force:
        clean(fetch=True)

    dependency_list = DependencyList()
    dependency_list.create_dependencies(args.path)
    dependency_list.create_subdependencies()
    dependency_list.fetch(output)
    dependency_list.check(output)

    output.write("Done\n")


def run_build(args: Namespace, output=sys.stdout):
    """Run the build command."""
    if args.force:
        clean(fetch=True, build=True)

    dependency_list = DependencyList(args.install_path)
    dependency_list.create_dependencies(args.path)
    dependency_list.create_subdependencies()
    dependency_list.fetch(output)
    dependency_list.check(output)
    dependency_list.build(args.rest, output)

    output.write("Done\n")


def run_install(args: Namespace, output=sys.stdout):
    """Run the install command."""
    if args.force:
        clean(fetch=True, build=True, install=True)

    dependency_list = DependencyList(args.install_path)
    dependency_list.create_dependencies(args.path)
    dependency_list.create_subdependencies()
    dependency_list.fetch(output)
    dependency_list.check(output)
    dependency_list.build(args.rest, output)
    dependency_list.install(output)

    output.write("Done\n\n")

    output.write(
        "You can now call CMake with "
        f"{CMAKE_PREFIX_PATH.format(dependency_list.get_install_path())}\n"
    )


def run_clean(args: Namespace, output=sys.stdout):
    """Run the clean command."""
    clean(
        fetch=args.fetch or args.all,
        build=args.build or args.all or not (args.fetch or args.build or args.install),
        install=args.install or args.all,
        install_path=args.install_path,
    )

    output.write("Cache cleaned\n")


def main():
    parser = get_parser()
    args = parser.parse_args()

    try:
        args.function(args)

    except DependenCmakeError as error:
        logger.critical(error)
        exit(1)


if __name__ == "__main__":
    main()
