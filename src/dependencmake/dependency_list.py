import sys
from dataclasses import dataclass, field
from typing import Iterator

from path import Path
from tqdm import tqdm

from dependencmake.cmake import check_cmake_exists
from dependencmake.config import check_config, ConfigNotFoundError, get_config
from dependencmake.dependency import Dependency
from dependencmake.filesystem import CACHE, CACHE_BUILD, CACHE_FETCH, CACHE_INSTALL


@dataclass
class DependencyList:
    """List of the dependencies of the project."""

    dependencies: list = field(default_factory=list)

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

        # fetch subdependencies
        output.write("Fetching subdependencies if any...\n")
        with tqdm(file=output, leave=False, unit="subdependency") as progress_bar:
            for subdependency in self.generate_subdependencies():
                subdependency.fetch()
                progress_bar.update()

    def build(self, extra_args: list = [], output=sys.stdout):
        """Build dependencies."""
        # create build cache
        CACHE_BUILD.mkdir_p()

        # check CMake works
        check_cmake_exists()

        # build
        output.write("Building dependencies...\n")
        for dependency in tqdm(
            self.dependencies, file=output, leave=False, unit="dependency"
        ):
            dependency.build(extra_args)

    def install(self, output=sys.stdout):
        """Install dependencies."""
        # create build cache
        CACHE_INSTALL.mkdir_p()

        # check CMake works
        check_cmake_exists()

        # build
        output.write("Installing dependencies...\n")
        for dependency in tqdm(
            self.dependencies, file=output, leave=False, unit="dependency"
        ):
            dependency.install()
