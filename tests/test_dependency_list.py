from io import StringIO
from unittest.mock import call

import pytest
from packaging import version
from path import Path

from dependencmake.dependency import Dependency
from dependencmake.dependency_list import DependencyList, DiamondDependencyError
from dependencmake.filesystem import CACHE, CACHE_BUILD, CACHE_FETCH, CACHE_INSTALL


@pytest.fixture
def dependency_list():
    dependency_list = DependencyList()
    dependency_list.dependencies = [
        Dependency(name="My dep 1", url="http://example.com/dep1"),
        Dependency(name="My dep 2", url="http://example.com/dep2"),
    ]

    return dependency_list


@pytest.fixture
def dependency_list_data():
    dependency_list = DependencyList()
    dependency_list.dependencies = [
        Dependency(
            name="My dep 1",
            url="http://example.com/dep1",
            cmake_project_name="Dep1",
            cmake_project_version=version.parse("1.2.0"),
        ),
        Dependency(
            name="My dep 1",
            url="http://example.com/dep2",
            cmake_project_name="Dep2",
            cmake_project_version=version.parse("2.4.0"),
        ),
    ]

    return dependency_list


class TestDependencyList:
    def test_create_dependencies(self, mocker):
        """Create dependencies from list."""
        mocked_get_config = mocker.patch("dependencmake.dependency_list.get_config")
        config = {
            "dependencies": [
                {"name": "My dep 1", "url": "http://example.com/dep1"},
                {"name": "My dep 2", "url": "http://example.com/dep2"},
            ]
        }
        mocked_get_config.return_value = config
        mocked_check_config = mocker.patch("dependencmake.dependency_list.check_config")

        dependency_list = DependencyList()
        assert len(dependency_list.dependencies) == 0
        dependency_list.create_dependencies(Path("path"))
        assert len(dependency_list.dependencies) == 2
        assert isinstance(dependency_list.dependencies[0], Dependency)
        assert isinstance(dependency_list.dependencies[1], Dependency)

        mocked_get_config.assert_called_with(Path("path"))
        mocked_check_config.assert_called_with(config)

    def test_describe(self, dependency_list, mocker):
        """Describe dependencies in list."""
        mocked_refresh = mocker.patch.object(Dependency, "refresh")
        mocked_describe = mocker.patch.object(Dependency, "describe")

        output = StringIO()
        dependency_list.describe(output)

        mocked_refresh.assert_called_with()
        mocked_describe.assert_called_with(output)

    def test_fetch(self, dependency_list, mocker):
        """Fetch dependencies in list."""
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_fetch = mocker.patch.object(Dependency, "fetch")
        mocked_set_cmake_project_data = mocker.patch.object(
            Dependency, "set_cmake_project_data"
        )

        output = StringIO()
        dependency_list.fetch(output)

        mocked_mkdir_p.assert_has_calls([call(CACHE), call(CACHE_FETCH)])
        mocked_fetch.assert_called_with()
        mocked_set_cmake_project_data.assert_called_with()

    def test_build(self, dependency_list, mocker):
        """Build dependencies in list."""
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_check_cmake_exists = mocker.patch(
            "dependencmake.dependency_list.check_cmake_exists"
        )
        mocked_build = mocker.patch.object(Dependency, "build")
        mocked_get_install_path = mocker.patch.object(
            DependencyList, "get_install_path"
        )
        mocked_get_install_path.return_value = Path("install")

        output = StringIO()
        dependency_list.build(["-DCMAKE_ARG=ON"], output)

        mocked_mkdir_p.assert_called_with(CACHE_BUILD)
        mocked_check_cmake_exists.assert_called_with()
        mocked_build.assert_called_with(Path("install"), ["-DCMAKE_ARG=ON"])

    def test_install(self, dependency_list, mocker):
        """Install dependencies in list."""
        mocked_makedirs_p = mocker.patch.object(Path, "makedirs_p", autospec=True)
        mocked_check_cmake_exists = mocker.patch(
            "dependencmake.dependency_list.check_cmake_exists"
        )
        mocked_install = mocker.patch.object(Dependency, "install")

        output = StringIO()
        dependency_list.install(output)

        mocked_makedirs_p.assert_called_with(CACHE_INSTALL)
        mocked_check_cmake_exists.assert_called_with()
        mocked_install.assert_called_with()

    def test_check(self, dependency_list_data):
        """Check dependencies in list."""
        output = StringIO()
        dependency_list_data.check(output)

    def test_check_diamond_dependencies_same_version(self, dependency_list_data):
        """Do not detect diamond dependency with same version during check."""
        dependency_list_data.dependencies[1].cmake_project_name = "Dep1"
        dependency_list_data.dependencies[1].cmake_project_version = version.parse(
            "1.2.0"
        )

        output = StringIO()
        dependency_list_data.check(output)

    def test_check_diamond_dependencies_same_url(self, dependency_list_data):
        """Do not detect diamond dependency with same url during check."""
        dependency_list_data.dependencies[1].cmake_project_name = "Dep1"
        dependency_list_data.dependencies[1].url = "http://example.com/dep1"

        output = StringIO()
        dependency_list_data.check(output)

    def test_check_diamond_dependencies_error(self, dependency_list_data):
        """Detect diamond dependency during check."""
        dependency_list_data.dependencies[1].cmake_project_name = "Dep1"

        with pytest.raises(DiamondDependencyError):
            output = StringIO()
            dependency_list_data.check(output)

    def test_get_install_directory_default(self, mocker):
        """Test to get default install directory."""
        mocked_realpath = mocker.patch.object(Path, "realpath", autospec=True)
        mocked_realpath.side_effect = lambda p: p

        dependency_list = DependencyList()

        assert dependency_list.get_install_path() == CACHE_INSTALL

    def test_get_install_directory_set(self, mocker):
        """Test to get specified install directory."""
        mocked_realpath = mocker.patch.object(Path, "realpath", autospec=True)
        mocked_realpath.side_effect = lambda p: p

        dependency_list = DependencyList(Path("lib"))

        assert dependency_list.get_install_path() == Path("lib")
