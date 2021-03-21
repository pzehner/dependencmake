from tempfile import TemporaryDirectory

try:
    from importlib.resources import path

except ImportError:
    from importlib_resources import path  # type: ignore

from path import Path

from dependencmake.dependency_list import DependencyList
from tests.test_main_integration import cd


class TestDependencyList:
    def test_create_subdependencies(self):
        """Create supdependencies."""
        with TemporaryDirectory() as temp_directory:
            temp_path = Path(temp_directory)
            test_path = temp_path / "test"
            with path("tests.resources.subdependencies", "") as resources_directory:
                resources_path = Path(resources_directory)
                resources_path.copytree(test_path)
                with cd(resources_path):
                    dependency_list = DependencyList()
                    dependency_list.create_dependencies(test_path)
                    dependency_list.create_subdependencies()

        assert len(dependency_list.dependencies) == 5
        assert dependency_list.dependencies[0].name == "Dep11"
        assert dependency_list.dependencies[1].name == "Dep12"
        assert dependency_list.dependencies[2].name == "Dep1"
        assert dependency_list.dependencies[3].name == "Dep21"
        assert dependency_list.dependencies[4].name == "Dep2"

    def test_fetch_subdependencies(self, mocker):
        """Fetch supdependencies."""
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.return_value = {"name": "Dep", "version": "1.0.0"}

        with TemporaryDirectory() as temp_directory:
            temp_path = Path(temp_directory)
            test_path = temp_path / "test"
            with path("tests.resources.subdependencies", "") as resources_directory:
                resources_path = Path(resources_directory)
                resources_path.copytree(test_path)
                with cd(resources_path):
                    dependency_list = DependencyList()
                    dependency_list.create_dependencies(test_path)
                    dependency_list.create_subdependencies()
                    dependency_list.fetch()
