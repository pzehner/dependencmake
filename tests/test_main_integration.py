from argparse import Namespace
from io import StringIO

try:
    from importlib.resources import path

except ImportError:
    from importlib_resources import path  # type: ignore

import pytest
from path import Path

from dependencmake.__main__ import run_build, run_fetch, run_install, run_list
from dependencmake.filesystem import CACHE_INSTALL


@pytest.fixture
def temp_directory(tmp_path):
    return Path(tmp_path)


class TestRunList:
    def test_run(self, temp_directory):
        """List dependencies."""
        # copy test files
        with path("tests.resources", "dependencmake.yaml") as config:
            Path(config).copy(temp_directory)

        # run test
        with temp_directory:
            args = Namespace(path=temp_directory)
            output = StringIO()
            run_list(args, output)


class TestRunFetch:
    def test_run(self, mocker, temp_directory):
        """Fetch dependencies."""
        mocker.patch("dependencmake.dependency.Repo")
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.side_effect = [
            {"name": "Dep1", "version": "1.0.0"},
            {"name": "Dep2", "version": "2.0.0"},
        ]

        # copy test files
        with path("tests.resources", "dependencmake.yaml") as config:
            Path(config).copy(temp_directory)

        # run test
        with temp_directory:
            args = Namespace(path=temp_directory, force=False)
            output = StringIO()
            run_fetch(args, output)


class TestRunBuild:
    def test_run(self, mocker, temp_directory):
        """Build dependencies."""
        mocker.patch("dependencmake.dependency.Repo")
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocker.patch("dependencmake.cmake.run")
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.side_effect = [
            {"name": "Dep1", "version": "1.0.0"},
            {"name": "Dep2", "version": "2.0.0"},
        ]

        # copy test files
        with path("tests.resources", "dependencmake.yaml") as config:
            Path(config).copy(temp_directory)

        # run test
        with temp_directory:
            args = Namespace(
                path=temp_directory, force=False, install_path=None, rest=[]
            )
            output = StringIO()
            run_build(args, output)

    def test_run_install_path(self, mocker, temp_directory):
        """Build dependencies with specific install path."""
        mocker.patch("dependencmake.dependency.Repo")
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocker.patch("dependencmake.cmake.run")
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.side_effect = [
            {"name": "Dep1", "version": "1.0.0"},
            {"name": "Dep2", "version": "2.0.0"},
        ]

        # copy test files
        with path("tests.resources", "dependencmake.yaml") as config:
            Path(config).copy(temp_directory)

        # run test
        with temp_directory:
            args = Namespace(
                path=temp_directory, force=False, install_path=Path("lib"), rest=[]
            )
            output = StringIO()
            run_build(args, output)


class TestRunInstall:
    def test_run(self, mocker, temp_directory):
        """Install dependencies."""
        mocker.patch("dependencmake.dependency.Repo")
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocker.patch("dependencmake.cmake.run")
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.side_effect = [
            {"name": "Dep1", "version": "1.0.0"},
            {"name": "Dep2", "version": "2.0.0"},
        ]

        # copy test files
        with path("tests.resources", "dependencmake.yaml") as config:
            Path(config).copy(temp_directory)

        # run test
        with temp_directory:
            args = Namespace(
                path=temp_directory, force=False, install_path=None, rest=[]
            )
            output = StringIO()
            run_install(args, output)

        content = output.getvalue()
        assert (
            "You can now call CMake with -DCMAKE_PREFIX_PATH="
            f"{temp_directory / CACHE_INSTALL}" in content
        )

    def test_run_install_path(self, mocker, temp_directory):
        """Install dependencies with specific install path."""
        mocker.patch("dependencmake.dependency.Repo")
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocker.patch("dependencmake.cmake.run")
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data"
        )
        mocked_get_project_data.side_effect = [
            {"name": "Dep1", "version": "1.0.0"},
            {"name": "Dep2", "version": "2.0.0"},
        ]

        # copy test files
        with path("tests.resources", "dependencmake.yaml") as config:
            Path(config).copy(temp_directory)

        # run test
        with temp_directory:
            args = Namespace(
                path=temp_directory, force=False, install_path=Path("lib"), rest=[]
            )
            output = StringIO()
            run_install(args, output)

        content = output.getvalue()
        assert (
            "You can now call CMake with -DCMAKE_PREFIX_PATH="
            f"{temp_directory / 'lib'}" in content
        )
