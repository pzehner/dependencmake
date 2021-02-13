import pytest
from io import StringIO
from shutil import ReadError
from unittest.mock import MagicMock
from urllib.request import HTTPError

from git import GitCommandError
from path import Path

from dependen6make.dependency import (
    ArchiveDecompressError,
    ArchiveDownloadError,
    Dependency,
    GitRepoFetchError,
    UnknownDependencyTypeError,
)
from dependen6make.filesystem import CACHE_FETCH


@pytest.fixture
def dependency():
    return Dependency(
        name="My dep",
        url="http://example.com/dependency",
        git_hash="424242",
        cmake_args="-DCMAKE_ARG=ON",
    )


@pytest.fixture
def git_dependency():
    return Dependency(
        name="My Git dep",
        url="http://example.com/dependency.git",
        git_hash="424242",
    )


@pytest.fixture
def zip_dependency():
    return Dependency(
        name="My zip dep",
        url="http://example.com/dependency.zip",
    )


class TestDependency:
    def test_create(self):
        """Create a dependency."""
        dependency = Dependency(
            name="My dep",
            url="http://example.com/dependency",
            git_hash="424242",
            cmake_args="-DCMAKE_ARG=ON",
        )
        assert dependency.name == "My dep"
        assert dependency.url == "http://example.com/dependency"
        assert dependency.git_hash == "424242"
        assert dependency.cmake_args == "-DCMAKE_ARG=ON"

    def test_create_partial_arguments(self):
        """Create a dependency with partial arguments."""
        dependency = Dependency(name="My dep", url="http://example.com/dependency")
        assert dependency.git_hash is None
        assert dependency.cmake_args is None

    def test_create_too_few_arguments(self):
        """Create a dependency with to few arguments."""
        with pytest.raises(TypeError):
            Dependency(name="My dep")

    def test_describe(self, dependency):
        """Describe a dependency."""
        output = StringIO()
        dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My dep",
            "URL: http://example.com/dependency",
            "Git hash: 424242",
            "CMake arguments: -DCMAKE_ARG=ON",
        ]

    def test_fetch_for_git(self, git_dependency, mocker):
        """Fetch in case of a Git repository."""
        mocked_fetch_git = mocker.patch.object(Dependency, "fetch_git")

        assert not git_dependency.fetched
        git_dependency.fetch()
        assert git_dependency.fetched

        mocked_fetch_git.assert_called_with()

    def test_fetch_for_archive(self, zip_dependency, mocker):
        """Fetch in case of a zip archive."""
        mocked_fetch_archive = mocker.patch.object(Dependency, "fetch_archive")

        zip_dependency.fetch()

        mocked_fetch_archive.assert_called_with()

    def test_fetch_unknown_type(self, dependency, mocker):
        """Fetch in case of a dependency of unknown type."""
        mocked_fetch_git = mocker.patch.object(Dependency, "fetch_git")

        with pytest.raises(UnknownDependencyTypeError):
            dependency.fetch()

        mocked_fetch_git.assert_not_called()

    def test_fetch_git_clone(self, git_dependency, mocker):
        """Fetch a Git repository for the first time."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_repo = mocker.patch("dependen6make.dependency.Repo")

        assert git_dependency.directory_name is None
        git_dependency.fetch_git()
        assert git_dependency.directory_name == "my_git_dep"

        mocked_exists.assert_called_with(CACHE_FETCH / "my_git_dep")
        mocked_mkdir_p.assert_called_with(CACHE_FETCH / "my_git_dep")
        mocked_repo.clone_from.assert_called_with(
            "http://example.com/dependency.git", CACHE_FETCH / "my_git_dep"
        )
        mocked_repo.return_value.remote.assert_not_called()
        mocked_repo.clone_from.return_value.commit.assert_called_with("424242")

    def test_fetch_git_clone_error(self, git_dependency, mocker):
        """Error when fetching a Git repository."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_repo = mocker.patch("dependen6make.dependency.Repo")
        mocked_repo.clone_from.side_effect = GitCommandError("error message", "000")

        with pytest.raises(
            GitRepoFetchError,
            match=r"Cannot fetch My Git dep at http://example.com/dependency.git",
        ):
            git_dependency.fetch_git()

    def test_fetch_git_pull(self, git_dependency, mocker):
        """Fetch a Git repository that has been already fetched."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_repo = mocker.patch("dependen6make.dependency.Repo")

        git_dependency.fetch_git()

        mocked_exists.assert_called_with(CACHE_FETCH / "my_git_dep")
        mocked_mkdir_p.assert_not_called()
        mocked_repo.clone_from.assert_not_called()
        mocked_repo.return_value.remote.assert_called_with()
        mocked_repo.return_value.commit.assert_called_with("424242")

    def test_fetch_archive_exists(self, mocker, zip_dependency):
        """Fetch an archive already fetched."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_urlretrieve = mocker.patch("dependen6make.dependency.urlretrieve")

        assert zip_dependency.directory_name is None
        zip_dependency.fetch_archive()
        assert (
            zip_dependency.directory_name
            == "my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7"
        )

        mocked_exists.assert_called_with(
            CACHE_FETCH / "my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7"
        )
        mocked_urlretrieve.assert_not_called()

    def test_fetch_archive(self, mocker, zip_dependency):
        """Fetch an archive."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_temporary_directory_class = mocker.patch(
            "dependen6make.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocked_urlretrieve = mocker.patch("dependen6make.dependency.urlretrieve")
        mocked_unpack_archive = mocker.patch("dependen6make.dependency.unpack_archive")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        zip_dependency.fetch_archive()

        mocked_mkdir_p.assert_called_with(Path("temp") / "extract")
        mocked_urlretrieve.assert_called_with(
            "http://example.com/dependency.zip", Path("temp") / "dependency.zip"
        )
        mocked_unpack_archive.assert_called_with(
            Path("temp") / "dependency.zip", Path("temp") / "extract"
        )
        mocked_move_decompress_path.assert_called_with(
            Path("temp") / "extract",
            CACHE_FETCH / "my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7",
        )

    def test_fetch_archive_download_error(self, mocker, zip_dependency):
        """Error when downloading an archive."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_temporary_directory_class = mocker.patch(
            "dependen6make.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocked_urlretrieve = mocker.patch("dependen6make.dependency.urlretrieve")
        mocked_urlretrieve.side_effect = HTTPError(
            "url", "000", "error", "hdrs", MagicMock()
        )
        mocked_unpack_archive = mocker.patch("dependen6make.dependency.unpack_archive")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        with pytest.raises(
            ArchiveDownloadError,
            match=r"Cannot download My zip dep at http://example.com/dependency.zip: "
            r".*error",
        ):
            zip_dependency.fetch_archive()

        mocked_unpack_archive.assert_not_called()
        mocked_move_decompress_path.assert_not_called()

    def test_fetch_archive_decompress_error(self, mocker, zip_dependency):
        """Error when decompressing an archive."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_temporary_directory_class = mocker.patch(
            "dependen6make.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocker.patch("dependen6make.dependency.urlretrieve")
        mocked_unpack_archive = mocker.patch("dependen6make.dependency.unpack_archive")
        mocked_unpack_archive.side_effect = ReadError("error")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        with pytest.raises(
            ArchiveDecompressError,
            match=r"Cannot decompress archive of My zip dep: .*error",
        ):
            zip_dependency.fetch_archive()

        mocked_move_decompress_path.assert_not_called()

    def test_move_decompress_path_single(self, mocker):
        """Move a single directory."""
        mocked_listdir = mocker.patch.object(Path, "listdir", autospec=True)
        mocked_listdir.return_value = [Path("temp") / "extract" / "my_dep"]
        mocked_move = mocker.patch.object(Path, "move", autospec=True)

        Dependency.move_decompress_path(Path("temp") / "extract", Path("destination"))

        mocked_listdir.assert_called_with(Path("temp") / "extract")
        mocked_move.assert_called_with(
            Path("temp") / "extract" / "my_dep", Path("destination")
        )

    def test_move_decompress_path_multiple(self, mocker):
        """Move several elements."""
        mocked_listdir = mocker.patch.object(Path, "listdir", autospec=True)
        mocked_listdir.return_value = [
            Path("temp") / "extract" / "file1",
            Path("temp") / "extract" / "file2",
        ]
        mocked_move = mocker.patch.object(Path, "move", autospec=True)

        Dependency.move_decompress_path(Path("temp") / "extract", Path("destination"))

        mocked_listdir.assert_called_with(Path("temp") / "extract")
        mocked_move.assert_called_with(Path("temp") / "extract", Path("destination"))

    def test_describe_after_fetch(self, zip_dependency, mocker):
        """Describe a dependency."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_temporary_directory_class = mocker.patch(
            "dependen6make.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocked_urlretrieve = mocker.patch("dependen6make.dependency.urlretrieve")
        mocked_unpack_archive = mocker.patch("dependen6make.dependency.unpack_archive")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        output = StringIO()
        zip_dependency.fetch()
        zip_dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My zip dep",
            "URL: http://example.com/dependency.zip",
            "Directory name: my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7",
            "Fetched"
        ]

    def test_refresh_git(self, git_dependency, mocker):
        """Refresh a Git dependency."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True

        assert git_dependency.directory_name is None
        assert not git_dependency.fetched
        git_dependency.refresh()
        assert git_dependency.directory_name == "my_git_dep"
        assert git_dependency.fetched

    def test_refresh_zip(self, zip_dependency, mocker):
        """Refresh an archive dependency."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True

        assert zip_dependency.directory_name is None
        assert not zip_dependency.fetched
        zip_dependency.refresh()
        assert zip_dependency.directory_name == "my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7"
        assert zip_dependency.fetched

    def test_refresh_unknown_type(self, dependency, mocker):
        """Refresh a dependency of unknown type."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True

        with pytest.raises(UnknownDependencyTypeError):
            dependency.refresh()
