try:
    from importlib.resources import path

except ImportError:
    from importlib_resources import path  # type: ignore

import pytest
from path import Path

from dependencmake.dependency_list import DependencyList


@pytest.fixture
def temp_directory(tmp_path):
    return Path(tmp_path)


@pytest.fixture
def subdependencies_temp_directory(temp_directory):
    with path("tests.resources.subdependencies", "dependencmake.yaml") as config:
        Path(config).copy(temp_directory)

    fetch_directory = (temp_directory / "dependencmake" / "fetch").makedirs_p()
    (fetch_directory / "dep11_1d264692d45516dcae4a8f07a847d742").mkdir_p()
    (fetch_directory / "dep12_fe8ba562a3f2c89af885e5036f465d4b").mkdir_p()
    dep1 = (fetch_directory / "dep1_36e47005e2edb6e84fdb0e2e411bff5a").mkdir_p()
    (fetch_directory / "dep21_d1efc308c741bb9421611de57b61aec2").mkdir_p()
    dep2 = (fetch_directory / "dep2_4b35bd592421ea9170dfb690d7550744").mkdir_p()

    resource = "tests.resources.subdependencies.dependencmake.fetch"

    with path(
        f"{resource}.dep1_36e47005e2edb6e84fdb0e2e411bff5a",
        "dependencmake.yaml",
    ) as config:
        Path(config).copy(dep1)

    with path(
        f"{resource}.dep2_4b35bd592421ea9170dfb690d7550744",
        "dependencmake.yaml",
    ) as config:
        Path(config).copy(dep2)

    return temp_directory


class TestDependencyList:
    def test_create_subdependencies(self, subdependencies_temp_directory):
        """Create supdependencies."""
        with subdependencies_temp_directory:
            dependency_list = DependencyList()
            dependency_list.create_dependencies(subdependencies_temp_directory)
            dependency_list.create_subdependencies()

        assert len(dependency_list.dependencies) == 5
        assert dependency_list.dependencies[0].name == "Dep11"
        assert dependency_list.dependencies[1].name == "Dep12"
        assert dependency_list.dependencies[2].name == "Dep1"
        assert dependency_list.dependencies[3].name == "Dep21"
        assert dependency_list.dependencies[4].name == "Dep2"

    def test_fetch_subdependencies(self, mocker, subdependencies_temp_directory):
        """Fetch supdependencies."""
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.return_value = {"name": "Dep", "version": "1.0.0"}

        with subdependencies_temp_directory:
            dependency_list = DependencyList()
            dependency_list.create_dependencies(subdependencies_temp_directory)
            dependency_list.create_subdependencies()
            dependency_list.fetch()
