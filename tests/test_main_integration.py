from argparse import Namespace
from io import StringIO
from tempfile import TemporaryDirectory

try:
    from importlib.resources import path

except ImportError:
    from importlib_resources import path  # type: ignore

from path import Path

from dependencmake.__main__ import run_build, run_fetch, run_install, run_list
from dependencmake.filesystem import CACHE_INSTALL


class TestRunList:
    def test_run(self):
        """List dependencies."""
        with path("tests.resources", "dependencmake.yaml") as config:
            directory_path = Path(config).parent
            args = Namespace(path=directory_path)
            output = StringIO()
            run_list(args, output)


class TestRunFetch:
    def test_run(self, mocker):
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

        with TemporaryDirectory() as temp_directory:
            with Path(temp_directory):
                with path("tests.resources", "dependencmake.yaml") as config:
                    directory_path = Path(config).parent
                    args = Namespace(path=directory_path, force=False)
                    output = StringIO()
                    run_fetch(args, output)


class TestRunBuild:
    def test_run(self, mocker):
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

        with TemporaryDirectory() as temp_directory:
            with Path(temp_directory):
                with path("tests.resources", "dependencmake.yaml") as config:
                    directory_path = Path(config).parent
                    args = Namespace(path=directory_path, force=False, rest=[])
                    output = StringIO()
                    run_build(args, output)


class TestRunInstall:
    def test_run(self, mocker):
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

        with TemporaryDirectory() as temp_directory:
            with Path(temp_directory):
                mocked_get_getcwd = mocker.patch.object(Path, "getcwd")
                mocked_get_getcwd.return_value = Path("directory")

                with path("tests.resources", "dependencmake.yaml") as config:
                    directory_path = Path(config).parent
                    args = Namespace(path=directory_path, force=False, rest=[])
                    output = StringIO()
                    run_install(args, output)

        content = output.getvalue()
        assert (
            f"You can now call CMake with -DCMAKE_PREFIX_PATH=directory/{CACHE_INSTALL}"
            in content
        )
