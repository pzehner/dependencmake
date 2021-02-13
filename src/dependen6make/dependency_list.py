import sys
from dataclasses import dataclass, field

from tqdm import tqdm

from dependen6make.dependency import Dependency
from dependen6make.filesystem import CACHE, CACHE_FETCH


@dataclass
class DependencyList:
    """List of the dependencies of the project."""

    dependencies: list = field(default_factory=list)

    def create_dependencies(self, raw_dependencies: list):
        """Set dependencies from list of dictionaries."""
        self.dependencies = [Dependency(**kwargs) for kwargs in raw_dependencies]

    def describe(self, output=sys.stdout):
        """Describe dependencies as text."""
        output.write("Dependencies listed in config\n\n")
        output.write("\n".rjust(40, "-"))

        for dependency in self.dependencies:
            dependency.refresh()
            dependency.describe(output)
            output.write("\n".rjust(40, "-"))

    def fetch(self, output=sys.stdout):
        """Fetch dependencies."""
        # create fetch cache
        CACHE.mkdir_p()
        CACHE_FETCH.mkdir_p()

        # fetch
        output.write("Fetching dependencies...\n")
        for dependency in tqdm(self.dependencies, file=output, leave=False):
            dependency.fetch()
