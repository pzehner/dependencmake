from io import StringIO
from re import escape
from shutil import ReadError
from unittest.mock import MagicMock, call
from urllib.error import HTTPError

import pytest
from furl import furl
from git import GitCommandError
from packaging import version
from path import Path

from dependencmake.cmake import CMakeBuildError, CMakeConfigureError, CMakeInstallError
from dependencmake.dependency import (
    ArchiveAccessError,
    ArchiveDecompressError,
    ArchiveDownloadError,
    ArchiveMoveError,
    BuildError,
    CMakeProjectDataNotFoundError,
    ConfigureError,
    Dependency,
    FolderAccessError,
    FolderCopyError,
    GitRepoFetchError,
    InstallError,
    UnknownDependencyTypeError,
)
from dependencmake.filesystem import CACHE_BUILD, CACHE_FETCH


@pytest.fixture
def dependency():
    return Dependency(
        name="My dep",
        url="http://example.com/dependency",
        git_hash="424242",
        cmake_args="-DCMAKE_ARG=ON",
        jobs=1,
    )


@pytest.fixture
def subdir_dependency():
    return Dependency(
        name="My dep", url="http://example.com/dependency", cmake_subdir="subdir"
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


@pytest.fixture
def folder_dependency():
    return Dependency(
        name="My dep",
        url="file:///home/me/dependency",
    )


@pytest.fixture
def local_zip_dependency():
    return Dependency(
        name="My zip dep",
        url="file:///home/me/dependency.zip",
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
        assert dependency.git_hash == ""
        assert dependency.cmake_args == ""

    def test_create_too_few_arguments(self):
        """Create a dependency with to few arguments."""
        with pytest.raises(TypeError):
            Dependency(name="My dep")

    def test_describe_dependency(self, dependency):
        """Describe a dependency."""
        output = StringIO()
        dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My dep",
            "URL: http://example.com/dependency",
            "Git hash: 424242",
            "CMake arguments: -DCMAKE_ARG=ON",
            "Jobs for building: 1",
            "",
            "Directory name: my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
        ]

    def test_describe_subdependency(self, dependency, zip_dependency):
        """Describe a subdependency."""
        dependency.parent = zip_dependency
        output = StringIO()
        dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My dep",
            "URL: http://example.com/dependency",
            "Git hash: 424242",
            "CMake arguments: -DCMAKE_ARG=ON",
            "Jobs for building: 1",
            "",
            "Dependency of: My zip dep",
            "Directory name: my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
        ]

    def test_describe_subdir(self, subdir_dependency):
        """Describe a dependency with CMake subdirectory."""
        output = StringIO()
        subdir_dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My dep",
            "URL: http://example.com/dependency",
            "Directory with CMake files: subdir",
            "",
            "Directory name: my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
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

    def test_fetch_for_folder(self, folder_dependency, mocker):
        """Fetch in case of a local folder."""
        mocked_fetch_folder = mocker.patch.object(Dependency, "fetch_folder")

        folder_dependency.fetch()

        mocked_fetch_folder.assert_called_with()

    def test_fetch_for_local_archive(self, local_zip_dependency, mocker):
        """Fetch in case of a local zip archive."""
        mocked_fetch_archive = mocker.patch.object(Dependency, "fetch_local_archive")

        local_zip_dependency.fetch()

        mocked_fetch_archive.assert_called_with()

    def test_fetch_unknown_http_type(self, dependency, mocker):
        """Fetch in case of a dependency of unknown type with HTTP scheme."""
        with pytest.raises(
            UnknownDependencyTypeError,
            match=escape(
                r"Unable to manage online dependency My dep of type (no extension)"
            ),
        ):
            dependency.fetch()

    def test_fetch_unknown_file_type(self, dependency, mocker):
        """Fetch in case of a dependency of unknown type with file scheme."""
        dependency.url = "file:///home/me/dependency.other"
        dependency.url_parsed = furl(dependency.url)
        with pytest.raises(
            UnknownDependencyTypeError,
            match=r"Unable to manage local dependency My dep of type .other",
        ):
            dependency.fetch()

    def test_fetch_unknown_scheme(self, dependency, mocker):
        """Fetch in case of a dependency of unknown scheme."""
        dependency.url = "unknown://my_server/dependency.zip"
        dependency.url_parsed = furl(dependency.url)
        with pytest.raises(
            UnknownDependencyTypeError,
            match=r"Unable to manage dependency My dep with scheme unknown",
        ):
            dependency.fetch()

    def test_fetch_git_clone(self, git_dependency, mocker):
        """Fetch a Git repository for the first time."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_repo = mocker.patch("dependencmake.dependency.Repo")

        git_dependency.fetch_git()

        mocked_exists.assert_called_with(
            CACHE_FETCH / "my_git_dep_b90b270cffae363d3b9ad048ba2482af"
        )
        mocked_mkdir_p.assert_called_with(
            CACHE_FETCH / "my_git_dep_b90b270cffae363d3b9ad048ba2482af"
        )
        mocked_repo.clone_from.assert_called_with(
            "http://example.com/dependency.git",
            CACHE_FETCH / "my_git_dep_b90b270cffae363d3b9ad048ba2482af",
        )
        mocked_repo.return_value.remote.assert_not_called()
        mocked_repo.clone_from.return_value.commit.assert_called_with("424242")

    def test_fetch_git_clone_error(self, git_dependency, mocker):
        """Error when fetching a Git repository."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_repo = mocker.patch("dependencmake.dependency.Repo")
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
        mocked_repo = mocker.patch("dependencmake.dependency.Repo")

        git_dependency.fetch_git()

        mocked_exists.assert_called_with(
            CACHE_FETCH / "my_git_dep_b90b270cffae363d3b9ad048ba2482af"
        )
        mocked_mkdir_p.assert_not_called()
        mocked_repo.clone_from.assert_not_called()
        mocked_repo.return_value.remote.assert_called_with()
        mocked_repo.return_value.commit.assert_called_with("424242")

    def test_fetch_git_pull_no_update(self, git_dependency, mocker):
        """Fetch a Git repository has updates disabled."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_repo = mocker.patch("dependencmake.dependency.Repo")
        git_dependency.git_no_update = True

        git_dependency.fetch_git()

        mocked_repo.clone_from.assert_not_called()
        mocked_repo.return_value.remote.assert_not_called()

    def test_fetch_archive_exists(self, mocker, zip_dependency):
        """Fetch an archive already fetched."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_urlretrieve = mocker.patch("dependencmake.dependency.urlretrieve")

        zip_dependency.fetch_archive()

        mocked_exists.assert_called_with(
            CACHE_FETCH / "my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7"
        )
        mocked_urlretrieve.assert_not_called()

    def test_fetch_archive(self, mocker, zip_dependency):
        """Fetch an archive."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_temporary_directory_class = mocker.patch(
            "dependencmake.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocked_urlretrieve = mocker.patch("dependencmake.dependency.urlretrieve")
        mocked_decompress = mocker.patch.object(Dependency, "decompress")
        mocked_decompress.return_value = Path("temp") / "extract"
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        zip_dependency.fetch_archive()

        mocked_urlretrieve.assert_called_with(
            "http://example.com/dependency.zip", Path("temp") / "dependency.zip"
        )
        mocked_decompress.assert_called_with(
            Path("temp") / "dependency.zip", Path("temp")
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
            "dependencmake.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocked_urlretrieve = mocker.patch("dependencmake.dependency.urlretrieve")
        mocked_urlretrieve.side_effect = HTTPError(
            "url", "000", "error", "hdrs", MagicMock()
        )
        mocked_decompress = mocker.patch.object(Dependency, "decompress")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        with pytest.raises(
            ArchiveDownloadError,
            match=r"Cannot download My zip dep at http://example.com/dependency.zip: "
            r".*error",
        ):
            zip_dependency.fetch_archive()

        mocked_decompress.assert_not_called()
        mocked_move_decompress_path.assert_not_called()

    def test_decompress(self, mocker, zip_dependency):
        """Decompress an archive."""
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_unpack_archive = mocker.patch("dependencmake.dependency.unpack_archive")

        decompress_path = zip_dependency.decompress(
            Path("dependency.zip"), Path("temp")
        )
        assert decompress_path == Path("temp") / "extract"

        mocked_mkdir_p.assert_called_with(Path("temp") / "extract")
        mocked_unpack_archive.assert_called_with(
            Path("dependency.zip"), Path("temp") / "extract"
        )

    def test_decompress_error(self, mocker, zip_dependency):
        """Error when decompressing an archive."""
        mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_unpack_archive = mocker.patch("dependencmake.dependency.unpack_archive")
        mocked_unpack_archive.side_effect = ReadError("error")

        with pytest.raises(
            ArchiveDecompressError,
            match=r"Cannot decompress archive of My zip dep: .*error",
        ):
            zip_dependency.decompress(Path("dependency.zip"), Path("temp"))

    def test_move_decompress_path_single(self, mocker, dependency):
        """Move a single directory."""
        mocked_listdir = mocker.patch.object(Path, "listdir", autospec=True)
        mocked_listdir.return_value = [Path("temp") / "extract" / "my_dep"]
        mocked_move = mocker.patch.object(Path, "move", autospec=True)

        dependency.move_decompress_path(Path("temp") / "extract", Path("destination"))

        mocked_listdir.assert_called_with(Path("temp") / "extract")
        mocked_move.assert_called_with(
            Path("temp") / "extract" / "my_dep", Path("destination")
        )

    def test_move_decompress_path_single_error(self, mocker, dependency):
        """Error when moving a single directory."""
        mocked_listdir = mocker.patch.object(Path, "listdir", autospec=True)
        mocked_listdir.return_value = [Path("temp") / "extract" / "my_dep"]
        mocked_move = mocker.patch.object(Path, "move", autospec=True)
        mocked_move.side_effect = OSError("error")

        with pytest.raises(
            ArchiveMoveError, match=r"Cannot move archive of My dep: error"
        ):
            dependency.move_decompress_path(
                Path("temp") / "extract", Path("destination")
            )

    def test_move_decompress_path_multiple(self, mocker, dependency):
        """Move several elements."""
        mocked_listdir = mocker.patch.object(Path, "listdir", autospec=True)
        mocked_listdir.return_value = [
            Path("temp") / "extract" / "file1",
            Path("temp") / "extract" / "file2",
        ]
        mocked_move = mocker.patch.object(Path, "move", autospec=True)

        dependency.move_decompress_path(Path("temp") / "extract", Path("destination"))

        mocked_listdir.assert_called_with(Path("temp") / "extract")
        mocked_move.assert_called_with(Path("temp") / "extract", Path("destination"))

    def test_fetch_folder(self, folder_dependency, mocker):
        """Fetch a local folder."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.side_effect = [False, True]
        mocked_copytree = mocker.patch.object(Path, "copytree", autospec=True)

        folder_dependency.fetch_folder()

        mocked_exists.assert_has_calls(
            [
                call(CACHE_FETCH / "my_dep_c1a8170a4b020c8d66673eda4859358f"),
                call(Path("/") / "home" / "me" / "dependency"),
            ]
        )
        mocked_copytree.assert_called_with(
            Path("/") / "home" / "me" / "dependency",
            CACHE_FETCH / "my_dep_c1a8170a4b020c8d66673eda4859358f",
        )

    def test_fetch_folder_exists(self, folder_dependency, mocker):
        """Fetch a local folder that already exists."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_copytree = mocker.patch.object(Path, "copytree", autospec=True)

        folder_dependency.fetch_folder()

        mocked_copytree.assert_not_called()

    def test_fetch_folder_error_not_found(self, folder_dependency, mocker):
        """Cannot find a local folder."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.side_effect = [False, False]
        mocked_copytree = mocker.patch.object(Path, "copytree", autospec=True)

        with pytest.raises(
            FolderAccessError,
            match=r"Cannot access My dep at file:///home/me/dependency: "
            "folder not found",
        ):
            folder_dependency.fetch_folder()

        mocked_copytree.assert_not_called()

    def test_fetch_folder_error_copy(self, folder_dependency, mocker):
        """Error when copying a local folder."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.side_effect = [False, True]
        mocked_copytree = mocker.patch.object(Path, "copytree", autospec=True)
        mocked_copytree.side_effect = OSError("error")

        with pytest.raises(
            FolderCopyError,
            match=r"Cannot copy My dep at file:///home/me/dependency: error",
        ):
            folder_dependency.fetch_folder()

    def test_fetch_local_archive(self, local_zip_dependency, mocker):
        """Fetch a local archive."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.side_effect = [False, True]
        mocked_temporary_directory_class = mocker.patch(
            "dependencmake.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocked_decompress = mocker.patch.object(Dependency, "decompress")
        mocked_decompress.return_value = Path("temp") / "extract"
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        local_zip_dependency.fetch_local_archive()

        mocked_exists.assert_has_calls(
            [
                call(CACHE_FETCH / "my_zip_dep_235f522e2a9eb791919890436bacb0ee"),
                call(Path("/") / "home" / "me" / "dependency.zip"),
            ]
        )
        mocked_decompress.assert_called_with(
            Path("/") / "home" / "me" / "dependency.zip", Path("temp")
        )
        mocked_move_decompress_path.assert_called_with(
            Path("temp") / "extract",
            CACHE_FETCH / "my_zip_dep_235f522e2a9eb791919890436bacb0ee",
        )

    def test_fetch_local_archive_exists(self, local_zip_dependency, mocker):
        """Fetch a local archive that already exists."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_decompress = mocker.patch.object(Dependency, "decompress")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        local_zip_dependency.fetch_local_archive()

        mocked_decompress.assert_not_called()
        mocked_move_decompress_path.assert_not_called()

    def test_fetch_local_archive_error_not_found(self, local_zip_dependency, mocker):
        """Cannot access a local archive."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.side_effect = [False, False]
        mocked_decompress = mocker.patch.object(Dependency, "decompress")
        mocked_move_decompress_path = mocker.patch.object(
            Dependency, "move_decompress_path"
        )

        with pytest.raises(
            ArchiveAccessError,
            match=r"Cannot access My zip dep at file:///home/me/dependency.zip: "
            "file not found",
        ):
            local_zip_dependency.fetch_local_archive()

        mocked_decompress.assert_not_called()
        mocked_move_decompress_path.assert_not_called()

    def test_describe_after_fetch(self, zip_dependency, mocker):
        """Describe a dependency."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_temporary_directory_class = mocker.patch(
            "dependencmake.dependency.TemporaryDirectory"
        )
        mocked_temporary_directory_class.return_value.__enter__.return_value = "temp"
        mocker.patch("dependencmake.dependency.urlretrieve")
        mocker.patch("dependencmake.dependency.unpack_archive")
        mocker.patch.object(Dependency, "move_decompress_path")

        output = StringIO()
        zip_dependency.fetch()
        zip_dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My zip dep",
            "URL: http://example.com/dependency.zip",
            "",
            "Directory name: my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7",
            "Fetched",
        ]

    def test_refresh_git(self, git_dependency, mocker):
        """Refresh a Git dependency."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True

        assert not git_dependency.fetched
        assert not git_dependency.built
        git_dependency.refresh()
        assert git_dependency.fetched
        assert git_dependency.built

    def test_refresh_zip(self, zip_dependency, mocker):
        """Refresh an archive dependency."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True

        assert not zip_dependency.fetched
        assert not zip_dependency.built
        zip_dependency.refresh()
        assert zip_dependency.fetched
        assert zip_dependency.built

    def test_build(self, mocker, dependency):
        """Build a dependency."""
        mocked_cmake_lists_file_exists = mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_cmake_configure = mocker.patch(
            "dependencmake.dependency.cmake_configure", autospec=True
        )
        mocked_cmake_build = mocker.patch(
            "dependencmake.dependency.cmake_build", autospec=True
        )
        mocker.patch("dependencmake.dependency.CPU_CORES", 1)

        assert not dependency.built
        dependency.build(Path("install"))
        assert dependency.build

        mocked_cmake_lists_file_exists.assert_called_with(
            CACHE_FETCH / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93"
        )
        mocked_cmake_configure.assert_called_with(
            CACHE_FETCH / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
            CACHE_BUILD / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
            Path("install"),
            ["-DCMAKE_ARG=ON"],
        )
        mocked_cmake_build.assert_called_with(
            CACHE_BUILD / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93", 1
        )

    def test_build_subdir(self, mocker, subdir_dependency):
        """Build a dependency with source in a subdirectory."""
        mocked_cmake_lists_file_exists = mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_cmake_configure = mocker.patch(
            "dependencmake.dependency.cmake_configure", autospec=True
        )
        mocked_cmake_build = mocker.patch(
            "dependencmake.dependency.cmake_build", autospec=True
        )
        mocker.patch("dependencmake.dependency.CPU_CORES", 1)

        subdir_dependency.build(Path("install"))

        mocked_cmake_lists_file_exists.assert_called_with(
            CACHE_FETCH / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93" / "subdir"
        )
        mocked_cmake_configure.assert_called_with(
            CACHE_FETCH / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93" / "subdir",
            CACHE_BUILD / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
            Path("install"),
            [],
        )
        mocked_cmake_build.assert_called_with(
            CACHE_BUILD / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93", 3
        )

    def test_build_extra_arguments(self, mocker, dependency):
        """Build a dependency with extra CMake arguments passed."""
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_cmake_configure = mocker.patch(
            "dependencmake.dependency.cmake_configure", autospec=True
        )
        mocker.patch("dependencmake.dependency.cmake_build", autospec=True)
        mocker.patch("dependencmake.dependency.CPU_CORES", 1)

        assert not dependency.built
        dependency.build(Path("install"), ["-DCMAKE_ARG1=ON", "-DCMAKE_ARG2=OFF"])
        assert dependency.build

        mocked_cmake_configure.assert_called_with(
            CACHE_FETCH / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
            CACHE_BUILD / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93",
            Path("install"),
            ["-DCMAKE_ARG=ON", "-DCMAKE_ARG1=ON", "-DCMAKE_ARG2=OFF"],
        )

    def test_build_error_configure(self, mocker, dependency):
        """Configure error when building a dependency."""
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocked_cmake_configure = mocker.patch(
            "dependencmake.dependency.cmake_configure", autospec=True
        )
        mocked_cmake_configure.side_effect = CMakeConfigureError("error")
        mocked_cmake_build = mocker.patch(
            "dependencmake.dependency.cmake_build", autospec=True
        )
        mocker.patch("dependencmake.dependency.CPU_CORES", 1)

        with pytest.raises(ConfigureError, match=r"Cannot configure My dep: error"):
            dependency.build(Path("install"))

        mocked_cmake_build.assert_not_called()

    def test_build_error_build(self, mocker, dependency):
        """Build error when building a dependency."""
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocker.patch("dependencmake.dependency.cmake_configure", autospec=True)
        mocked_cmake_build = mocker.patch(
            "dependencmake.dependency.cmake_build", autospec=True
        )
        mocked_cmake_build.side_effect = CMakeBuildError("error")
        mocker.patch("dependencmake.dependency.CPU_CORES", 1)

        with pytest.raises(BuildError, match=r"Cannot build My dep: error"):
            dependency.build(Path("install"))

    def test_describe_after_build(self, zip_dependency, mocker):
        """Describe a dependency after build."""
        mocker.patch(
            "dependencmake.dependency.check_cmake_lists_file_exists", autospec=True
        )
        mocker.patch("dependencmake.cmake.run")

        output = StringIO()
        zip_dependency.build(Path("install"))
        zip_dependency.describe(output)
        lines = output.getvalue().splitlines()
        assert lines == [
            "Name: My zip dep",
            "URL: http://example.com/dependency.zip",
            "",
            "Directory name: my_zip_dep_355bfa4061a06c4d22ad5df3d74233a7",
            "Built",
        ]

    def test_install(self, mocker, dependency):
        """Install a dependency."""
        mocked_cmake_install = mocker.patch(
            "dependencmake.dependency.cmake_install", autospec=True
        )

        assert not dependency.installed
        dependency.install()
        assert dependency.installed

        mocked_cmake_install.assert_called_with(
            CACHE_BUILD / "my_dep_6dff8f0c30c3a3e97685b1c89e0baf93"
        )

    def test_install_error(self, mocker, dependency):
        """Error when installing a dependency."""
        mocked_cmake_install = mocker.patch(
            "dependencmake.dependency.cmake_install", autospec=True
        )
        mocked_cmake_install.side_effect = CMakeInstallError("error")

        with pytest.raises(InstallError, match=r"Cannot install My dep: error"):
            dependency.install()

    def test_set_cmake_project_data(self, mocker, dependency):
        """Set dependency CMake data."""
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data", autoset=True
        )
        mocked_get_project_data.return_value = {
            "name": "MyProjectName",
            "version": "1.2.0",
        }

        assert not dependency.cmake_project_name
        assert dependency.cmake_project_version is None
        dependency.set_cmake_project_data()
        assert dependency.cmake_project_name == "MyProjectName"
        assert dependency.cmake_project_version == version.parse("1.2.0")

    def test_set_cmake_project_data_no_version(self, mocker, dependency):
        """Set dependency CMake data without version."""
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data", autoset=True
        )
        mocked_get_project_data.return_value = {
            "name": "MyProjectName",
            "version": None,
        }

        assert dependency.cmake_project_version is None
        dependency.set_cmake_project_data()
        assert dependency.cmake_project_version is None

    def test_set_cmake_project_data_not_found(self, mocker, dependency):
        """Unable to set dependency CMake data."""
        mocked_get_project_data = mocker.patch(
            "dependencmake.dependency.get_project_data", autoset=True
        )
        mocked_get_project_data.return_value = None

        with pytest.raises(CMakeProjectDataNotFoundError):
            dependency.set_cmake_project_data()
