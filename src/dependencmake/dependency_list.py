import sys
from dataclasses import dataclass, field
from typing import Iterator

from path import Path
from tqdm import tqdm

from dependencmake.cmake import check_cmake_exists
from dependencmake.config import ConfigNotFoundError, check_config, get_config
from dependencmake.dependency import Dependency
from dependencmake.exceptions import DependenCmakeError
from dependencmake.filesystem import CACHE, CACHE_BUILD, CACHE_FETCH, CACHE_INSTALL


@dataclass
class DependencyList:
    """List of the dependencies of the project."""

    install_path: Path = CACHE_INSTALL
    dependencies: list = field(default_factory=list)

    def __post_init__(self):
        self.install_path = self.install_path or CACHE_INSTALL

    def create_dependencies(self, path: Path):
        """Set dependencies from config file in given path."""
        config = get_config(path)
        check_config(config)
        self.dependencies = [Dependency(**kwargs) for kwargs in config["dependencies"]]

    def create_subdependencies(self):
        """Set subdependencies from config files in fetch cache."""
        for _ in self.generate_subdependencies():
            pass

    def generate_subdependencies(self) -> Iterator[Dependency]:
        """Generate dependencies recursively.

        The iterator explores file system for config files to get the
        subdependencies. Dependencies must have been fetched beforehand.
        """
        # generate the dependencies list in revers order
        self.dependencies.reverse()
        i = 0
        while i != len(self.dependencies):
            dependency = self.dependencies[i]
            # load config file if any or move to next dependency
            try:
                dependency_config = get_config(CACHE_FETCH / dependency.directory_name)

            except ConfigNotFoundError:
                i += 1
                continue

            check_config(dependency_config)

            # create subdependendencies from dependency config
            subdependencies = [
                Dependency(**kwargs, parent=dependency)
                for kwargs in dependency_config["dependencies"]
            ]
            subdependencies.reverse()
            # add supdependencies to the dependency list
            # they will be listed before the parent dependency
            self.dependencies[i + 1 : i + 1] = subdependencies
            for subdependency in subdependencies:
                yield subdependency

            i += 1

        self.dependencies.reverse()

    def describe(self, output=sys.stdout):
        """Describe dependencies as text."""
        line = "\n".rjust(40, "-")
        output.write("Dependencies listed in config\n\n")
        output.write(line)

        for dependency in self.dependencies:
            dependency.refresh()
            dependency.describe(output)
            output.write(line)

    def fetch(self, output=sys.stdout):
        """Fetch dependencies."""
        # create fetch cache
        CACHE.mkdir_p()
        CACHE_FETCH.mkdir_p()

        # fetch immediate dependencies
        output.write("Fetching dependencies...\n")
        for dependency in tqdm(
            self.dependencies, file=output, leave=False, unit="dependency"
        ):
            dependency.fetch()
            dependency.set_cmake_project_data()

        # fetch subdependencies
        output.write("Fetching subdependencies if any...\n")
        with tqdm(file=output, leave=False, unit="subdependency") as progress_bar:
            for subdependency in self.generate_subdependencies():
                subdependency.fetch()
                subdependency.set_cmake_project_data()
                progress_bar.update()

    def check(self, output=sys.stdout):
        """Check dependencies for impossible to manage patterns."""
        output.write("Checking dependencies...\n")

        for dependency in tqdm(
            self.dependencies, file=output, leave=False, unit="dependency"
        ):
            # check diamond dependencies
            for other_dependency in self.dependencies:
                if other_dependency is dependency:
                    continue

                if dependency.cmake_project_name == other_dependency.cmake_project_name:
                    # pass if the two versions exist and are the same
                    if (
                        dependency.cmake_project_version
                        and dependency.cmake_project_version
                        == other_dependency.cmake_project_version
                    ):
                        continue

                    # pass if the two URLs and commit hash are the same
                    if (
                        dependency.url == other_dependency.url
                        and dependency.git_hash == other_dependency.git_hash
                    ):
                        continue

                    raise DiamondDependencyError(
                        "Diamond dependency detected with two different versions:\n\n"
                        f"{dependency.get_description()}\n\nand:\n\n"
                        f"{other_dependency.get_description()}"
                    )

    def get_install_path(self) -> Path:
        """Get a resolved version of the install path."""
        return self.install_path.realpath()

    def build(self, extra_args: list = [], output=sys.stdout):
        """Configure and build dependencies."""
        # create build cache
        CACHE_BUILD.mkdir_p()

        # check CMake works
        check_cmake_exists()

        # build
        output.write("Building dependencies...\n")
        for dependency in tqdm(
            self.dependencies, file=output, leave=False, unit="dependency"
        ):
            dependency.build(self.get_install_path(), extra_args)

    def install(self, output=sys.stdout):
        """Install dependencies."""
        # create build cache
        self.install_path.makedirs_p()

        # check CMake works
        check_cmake_exists()

        # build
        output.write("Installing dependencies...\n")
        for dependency in tqdm(
            self.dependencies, file=output, leave=False, unit="dependency"
        ):
            dependency.install()


class DiamondDependencyError(DependenCmakeError):
    pass
