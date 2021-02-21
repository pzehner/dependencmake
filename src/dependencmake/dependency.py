import hashlib
import sys
from dataclasses import dataclass
from multiprocessing import cpu_count
from shutil import get_unpack_formats, ReadError, unpack_archive
from tempfile import TemporaryDirectory
from typing import Optional
from urllib.error import HTTPError
from urllib.request import urlretrieve

from furl import furl
from git import GitCommandError, Repo
from path import Path

from dependencmake.cmake import (
    check_cmake_lists_file_exists,
    cmake_build,
    cmake_configure,
    cmake_install,
    CMakeBuildError,
    CMakeConfigureError,
    CMakeInstallError,
)
from dependencmake.exceptions import DependenCmakeError
from dependencmake.filesystem import CACHE_BUILD, CACHE_FETCH, CACHE_INSTALL


ARCHIVE_EXTENSIONS = [ext for format in get_unpack_formats() for ext in format[1]]
CPU_CORES = cpu_count()


@dataclass
class Dependency:
    """Dependency for the project."""

    name: str
    url: str
    git_hash: str = ""
    cmake_subdir: Optional[Path] = None
    cmake_args: str = ""
    jobs: int = 0
    parent: Optional["Dependency"] = None
    directory_name: str = ""
    url_parsed: furl = None
    fetched: bool = False
    built: bool = False
    installed: bool = False

    def __post_init__(self):
        # parse URL
        self.url_parsed = furl(self.url)

        # set directory name
        self.directory_name = f"{self.get_slug_name()}_{self.get_hash_url()}"

    def get_slug_name(self) -> str:
        """Get a slugified name of the dependency."""
        return "_".join(self.name.lower().split())

    def get_hash_url(self) -> str:
        """Get a hashed URL of the dependency."""
        return hashlib.md5(self.url.encode()).hexdigest()

    def get_extension(self) -> str:
        """Get extension in the URL."""
        return Path(self.url_parsed.path.segments[-1]).ext

    def refresh(self):
        """Refresh state of dependency based on cache content."""
        # get fetched status based on cache
        if (CACHE_FETCH / self.directory_name).exists():
            self.fetched = True

        # get built status based on cache
        if (CACHE_BUILD / self.directory_name).exists():
            self.built = True

    def describe(self, output=sys.stdout):
        """Describe dependency in text."""
        output.write(f"Name: {self.name}\n")
        output.write(f"URL: {self.url}\n")

        if self.git_hash:
            output.write(f"Git hash: {self.git_hash}\n")

        if self.cmake_subdir:
            output.write(f"Directory with CMake files: {self.cmake_subdir}\n")

        if self.cmake_args:
            output.write(f"CMake arguments: {self.cmake_args}\n")

        if self.jobs:
            output.write(f"Jobs for building: {self.jobs}\n")

        output.write("\n")

        if self.parent:
            output.write(f"Dependency of: {self.parent.name}\n")

        output.write(f"Directory name: {self.directory_name}\n")

        if self.fetched:
            output.write("Fetched\n")

        if self.built:
            output.write("Built\n")

    def fetch(self):
        """Fetch the dependency according to its type.

        Types are for now limited to Git repository, online archive file, local
        plain directory or local archive file.
        """
        scheme = self.url_parsed.scheme
        extension = self.get_extension()

        if scheme in ["http", "https"]:
            if extension == ".git":
                self.fetch_git()

            elif extension in ARCHIVE_EXTENSIONS:
                self.fetch_archive()

            else:
                raise UnknownDependencyTypeError(
                    f"Unable to manage online dependency {self.name} of "
                    f"type {extension or '(no extension)'}"
                )

        elif scheme == "file":
            if not extension:
                self.fetch_folder()

            elif extension in ARCHIVE_EXTENSIONS:
                self.fetch_local_archive()

            else:
                raise UnknownDependencyTypeError(
                    f"Unable to manage local dependency {self.name} of type {extension}"
                )

        else:
            raise UnknownDependencyTypeError(
                f"Unable to manage dependency {self.name} with scheme {scheme}"
            )

        # mark as fetched
        self.fetched = True

    def fetch_git(self):
        """Fetch a Git repository and checkout to the requested hash if necessary."""
        path = CACHE_FETCH / self.directory_name

        try:
            # clone if the path doesn't exist, or pull
            if not path.exists():
                path.mkdir_p()
                repo = Repo.clone_from(self.url, path)

            else:
                repo = Repo(path)
                repo.head.reference = repo.heads[0]
                repo.remote().pull()

            # checkout if requested
            if self.git_hash:
                repo.head.reference = repo.commit(self.git_hash)

        except GitCommandError as error:
            raise GitRepoFetchError(
                f"Cannot fetch {self.name} at {self.url}: {error}"
            ) from error

    def fetch_archive(self):
        """Fech an online archive and decompress it."""
        path = CACHE_FETCH / self.directory_name

        # download if the path doesn't exist, or do nothing otherwise
        if path.exists():
            return

        with TemporaryDirectory() as temp_directory:
            archive_path = Path(temp_directory) / self.url_parsed.path.segments[-1]

            # download file
            try:
                urlretrieve(self.url, archive_path)

            except HTTPError as error:
                raise ArchiveDownloadError(
                    f"Cannot download {self.name} at {self.url}: {error}"
                ) from error

            # decompress and move to destination
            decompress_path = self.decompress(archive_path, Path(temp_directory))
            self.move_decompress_path(decompress_path, path)

    def fetch_folder(self):
        """Fetch a local folder and copy it."""
        path = CACHE_FETCH / self.directory_name
        folder_path = Path(self.url_parsed.path)

        # copy if the path doesn't exist, or do nothing otherwise
        if path.exists():
            return

        # check target folder exists
        if not folder_path.exists():
            raise FolderAccessError(
                f"Cannot access {self.name} at {self.url}: folder not found"
            )

        try:
            folder_path.copytree(path)

        except OSError as error:
            raise FolderCopyError(
                f"Cannot copy {self.name} at {self.url}: {error}"
            ) from error

    def fetch_local_archive(self):
        """Decompress a local archive."""
        path = CACHE_FETCH / self.directory_name
        archive_path = Path(self.url_parsed.path)

        # fetch if the path doesn't exist, or do nothing otherwise
        if path.exists():
            return

        # check target folder exists
        if not archive_path.exists():
            raise ArchiveAccessError(
                f"Cannot access {self.name} at {self.url}: file not found"
            )

        with TemporaryDirectory() as temp_directory:
            # decompress and move to destination
            decompress_path = self.decompress(archive_path, Path(temp_directory))
            self.move_decompress_path(decompress_path, path)

    def decompress(self, archive_path: Path, temp_path: Path) -> Path:
        """Decompress an archive in a temporary directory, then move it."""
        # decompress file in a special directory, as we cannot list the
        # content of the archive
        decompress_path = temp_path / "extract"
        decompress_path.mkdir_p()

        try:
            unpack_archive(archive_path, decompress_path)

        except ReadError as error:
            raise ArchiveDecompressError(
                f"Cannot decompress archive of {self.name}: {error}"
            ) from error

        return decompress_path

    def move_decompress_path(self, decompress_path: Path, destination_path: Path):
        """Move the decompress directory to destination.

        If the decompress directory contains one directory, move this
        directory. If it contains multiple files, move the decompress directory
        instead.
        """
        decompress_files_paths = decompress_path.listdir()
        if len(decompress_files_paths) == 1:
            to_move_path = decompress_files_paths[0]

        else:
            to_move_path = decompress_path

        # move to fetch directory
        try:
            to_move_path.move(destination_path)

        except OSError as error:
            raise ArchiveMoveError(
                f"Cannot move archive of {self.name}: {error}"
            ) from error

    def build(self, extra_args: list = []):
        """Build the dependency."""
        # set source directory
        source_directory = CACHE_FETCH / self.directory_name

        if self.cmake_subdir:
            source_directory /= self.cmake_subdir

        # check there is a CMakeLists.txt file in it
        check_cmake_lists_file_exists(source_directory)

        # configure
        try:
            cmake_configure(
                source_directory,
                CACHE_BUILD / self.directory_name,
                CACHE_INSTALL,
                [*self.cmake_args.split(), *extra_args],
            )

        except CMakeConfigureError as error:
            raise ConfigureError(f"Cannot configure {self.name}: {error}") from error

        # build
        try:
            cmake_build(
                CACHE_BUILD / self.directory_name, self.jobs or (CPU_CORES * 2 + 1)
            )

        except CMakeBuildError as error:
            raise BuildError(f"Cannot build {self.name}: {error}") from error

        # mark as built
        self.built = True

    def install(self):
        """Install the dependency."""
        try:
            cmake_install(CACHE_BUILD / self.directory_name)

        except CMakeInstallError as error:
            raise InstallError(f"Cannot install {self.name}: {error}") from error

        # mark as installed
        self.installed = True


class UnknownDependencyTypeError(DependenCmakeError):
    pass


class ArchiveDownloadError(DependenCmakeError):
    pass


class ArchiveDecompressError(DependenCmakeError):
    pass


class ArchiveMoveError(DependenCmakeError):
    pass


class ArchiveAccessError(DependenCmakeError):
    pass


class GitRepoFetchError(DependenCmakeError):
    pass


class FolderAccessError(DependenCmakeError):
    pass


class FolderCopyError(DependenCmakeError):
    pass


class ConfigureError(DependenCmakeError):
    pass


class BuildError(DependenCmakeError):
    pass


class InstallError(DependenCmakeError):
    pass
