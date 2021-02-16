from argparse import Namespace
from contextlib import contextmanager
from importlib import resources
from io import StringIO
from tempfile import TemporaryDirectory

from path import Path

from dependencmake.__main__ import run_build, run_fetch, run_install, run_list
from dependencmake.filesystem import CACHE_INSTALL


@contextmanager
def cd(path: Path):
    """Temporarily cd to a directory."""
    previous = Path.getcwd()
    try:
        path.cd()
        yield None

    finally:
        previous.cd()


class TestRunList:
    def test_run(self):
        """List dependencies."""
        with resources.path("tests.resources", "") as directory:
            directory_path = Path(directory)
            args = Namespace(path=directory_path)
            output = StringIO()
            run_list(args, output)


class TestRunFetch:
    def test_run(self, mocker):
        """Fetch dependencies."""
        mocker.patch("dependencmake.dependency.Repo")
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")

        with TemporaryDirectory() as temp_directory:
            with cd(Path(temp_directory)):
                with resources.path("tests.resources", "") as directory:
                    directory_path = Path(directory)
                    args = Namespace(path=directory_path)
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

        with TemporaryDirectory() as temp_directory:
            with cd(Path(temp_directory)):
                with resources.path("tests.resources", "") as directory:
                    directory_path = Path(directory)
                    args = Namespace(path=directory_path)
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

        with TemporaryDirectory() as temp_directory:
            with cd(Path(temp_directory)):
                mocked_get_getcwd = mocker.patch.object(Path, "getcwd")
                mocked_get_getcwd.return_value = Path("directory")

                with resources.path("tests.resources", "") as directory:
                    directory_path = Path(directory)
                    args = Namespace(path=directory_path)
                    output = StringIO()
                    run_install(args, output)

        content = output.getvalue()
        assert (
            f"You can now call CMake with -DCMAKE_PREFIX_PATH=directory/{CACHE_INSTALL}"
            in content
        )
