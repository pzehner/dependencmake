from subprocess import DEVNULL, PIPE, CalledProcessError

import pytest
from path import Path

from dependencmake.cmake import (
    CMakeBuildError,
    CMakeConfigureError,
    CMakeInstallError,
    CMakeListsFileNotFound,
    CMakeNotFoundError,
    CMakeNotUseableError,
    check_cmake_exists,
    check_cmake_lists_file_exists,
    cmake_build,
    cmake_configure,
    cmake_install,
    get_output,
    get_project_data,
)


class TestCheckCMakeExists:
    def test_check(self, mocker):
        """CMake was found."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)

        check_cmake_exists()

        mocked_run.assert_called_with(
            ["cmake", "--version"], stdout=DEVNULL, stderr=DEVNULL, check=True
        )

    def test_check_error_not_found(self, mocker):
        """CMake was not found."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)
        mocked_run.side_effect = FileNotFoundError("not found")

        with pytest.raises(CMakeNotFoundError, match=r"CMake executable was not found"):
            check_cmake_exists()

    def test_check_error(self, mocker):
        """CMake cannot be run."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)
        mocked_run.side_effect = CalledProcessError(
            returncode=128, cmd="cmd", output=None, stderr=None
        )

        with pytest.raises(
            CMakeNotUseableError, match=r"CMake executable cannot be run"
        ):
            check_cmake_exists()


class TestCmakeListsFileExists:
    def test_check(self, mocker):
        """CMake lists file exists."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True

        check_cmake_lists_file_exists(Path("path"))

        mocked_exists.assert_called_with(Path("path") / "CMakeLists.txt")

    def test_check_not_found(self, mocker):
        """CMake lists file doesn't exist."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False

        with pytest.raises(
            CMakeListsFileNotFound, match=r"CMakeLists.txt not found in path"
        ):
            check_cmake_lists_file_exists(Path("path"))


class TestCMakeConfigure:
    def test_configure(self, mocker):
        """Configure a project."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)

        cmake_configure(
            Path("source"),
            Path("build"),
            Path("install"),
            ["arg1", "arg2"],
        )

        mocked_run.assert_called_with(
            [
                "cmake",
                "-DCMAKE_INSTALL_PREFIX=install",
                "-DCMAKE_PREFIX_PATH=install",
                "arg1",
                "arg2",
                "-S",
                "source",
                "-B",
                "build",
            ],
            stdout=PIPE,
            stderr=PIPE,
            check=True,
        )

    def test_configure_error(self, mocker):
        """Error when configuring a project."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)
        mocked_run.side_effect = CalledProcessError(
            returncode=128,
            cmd="cmd",
            output="stdout".encode(),
            stderr="stderr".encode(),
        )

        with pytest.raises(
            CMakeConfigureError, match=r"Configuration failed with code 128: stderr"
        ):
            cmake_configure(
                Path("source"),
                Path("build"),
                Path("install"),
                ["arg1", "arg2"],
            )


class TestCMakeBuild:
    def test_build(self, mocker):
        """Build a project."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)

        cmake_build(
            Path("build"),
            17,
        )

        mocked_run.assert_called_with(
            [
                "cmake",
                "--build",
                "build",
                "--parallel",
                "17",
            ],
            stdout=PIPE,
            stderr=PIPE,
            check=True,
        )

    def test_build_error(self, mocker):
        """Error when building a project."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)
        mocked_run.side_effect = CalledProcessError(
            returncode=128,
            cmd="cmd",
            output="stdout".encode(),
            stderr="stderr".encode(),
        )

        with pytest.raises(
            CMakeBuildError, match=r"Build failed with code 128: stderr"
        ):
            cmake_build(
                Path("build"),
                17,
            )


class TestCMakeInstall:
    def test_install(self, mocker):
        """Install a project."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)

        cmake_install(
            Path("build"),
        )

        mocked_run.assert_called_with(
            [
                "cmake",
                "--install",
                "build",
            ],
            stdout=PIPE,
            stderr=PIPE,
            check=True,
        )

    def test_install_error(self, mocker):
        """Error when installing a project."""
        mocked_run = mocker.patch("dependencmake.cmake.run", autospec=True)
        mocked_run.side_effect = CalledProcessError(
            returncode=128,
            cmd="cmd",
            output="stdout".encode(),
            stderr="stderr".encode(),
        )

        with pytest.raises(
            CMakeInstallError, match=r"Install failed with code 128: stderr"
        ):
            cmake_install(
                Path("build"),
            )


class TestGetOutput:
    def test_get_quiet(self):
        """Test to get quiet output."""
        assert get_output(True) == PIPE

    def test_get_verbose(self):
        """Test to get verbose output."""
        assert get_output(False) is None


class TestGetProjectDate:
    def test_get_none(self, mocker):
        """Unable to get project data."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = ""

        data = get_project_data(Path("path"))
        assert data is None

        mocked_read_text.assert_called_with(Path("path") / "CMakeLists.txt")

    def test_get_single_line_name(self, mocker):
        """Get project name as single line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] is None

    def test_get_single_line_name_space(self, mocker):
        """Get project name as single line with extra spaces."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project ( MyProject )"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] is None

    def test_get_single_line_name_version(self, mocker):
        """Get project name and version as single line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject VERSION 0.0)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_single_line_name_other_version(self, mocker):
        """Get project name and version as single line with other data inbetween."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = (
            """project(MyProject DESCRIPTION "Project description text" VERSION 0.0)"""
        )

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_single_line_name_other_version_other(self, mocker):
        """Get project name and version as single line with other data after."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = (
            """project(MyProject DESCRIPTION "Project description text" """
            """VERSION 0.0 LANGUAGES Fortran)"""
        )

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_multi_line_name(self, mocker):
        """Get project name as multi line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(
    MyProject
)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] is None

    def test_get_multi_line_name_version(self, mocker):
        """Get project name and version as multi line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(
    MyProject
    VERSION
        0.0
)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_multi_line_name_version_other(self, mocker):
        """Get project name and version as multi line with other data inbetween."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(
    MyProject
    DESCRIPTION
        "Project name text"
    VERSION
        0.0
)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_multi_line_name_version_other_after(self, mocker):
        """Get project name and version as multi line with other data after."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(
    MyProject
    DESCRIPTION
        "Project name text"
    VERSION
        0.0
    LANGUAGES
        Fortran
)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_mixed_line_name_version_other_after(self, mocker):
        """Get project name and version as mixed line with other data after."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject
    DESCRIPTION
        "Project name text"
    VERSION
        0.0
    LANGUAGES
        Fortran
)"""

        data = get_project_data(Path("path"))
        assert data["name"] == "MyProject"
        assert data["version"] == "0.0"

    def test_get_project_version_single_line_version(self, mocker):
        """Get project version from PROJECT_VERISION as single line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject)

set(PROJECT_VERSION 0.0)"""

        data = get_project_data(Path("path"))
        assert data["version"] == "0.0"

    def test_get_cmake_project_version_single_line_version(self, mocker):
        """Get project version from CMAKE_PROJECT_VERSION as single line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject)

set(CMAKE_PROJECT_VERSION 0.0)"""

        data = get_project_data(Path("path"))
        assert data["version"] == "0.0"

    def test_get_project_version_multi_line_version(self, mocker):
        """Get project version from PROJECT_VERISION as multi line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject)

set(
    PROJECT_VERSION
    0.0
)"""

        data = get_project_data(Path("path"))
        assert data["version"] == "0.0"

    def test_get_cmake_project_version_multi_line_version(self, mocker):
        """Get project version from CMAKE_PROJECT_VERSION as multi line."""
        mocked_read_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_read_text.return_value = """project(MyProject)

set(
    CMAKE_PROJECT_VERSION
    0.0
)"""

        data = get_project_data(Path("path"))
        assert data["version"] == "0.0"
