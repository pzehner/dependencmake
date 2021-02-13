from argparse import Namespace
from contextlib import contextmanager
from importlib import resources
from io import StringIO
from tempfile import TemporaryDirectory

from path import Path

from dependen6make.__main__ import run_fetch, run_list


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
        mocker.patch("dependen6make.dependency.Repo")
        mocker.patch("dependen6make.dependency.urlretrieve")
        mocker.patch("dependen6make.dependency.unpack_archive")

        with TemporaryDirectory() as temp_directory:
            with cd(Path(temp_directory)):
                with resources.path("tests.resources", "") as directory:
                    directory_path = Path(directory)
                    args = Namespace(path=directory_path)
                    output = StringIO()
                    run_fetch(args, output)
