import hashlib
import sys
from dataclasses import dataclass
from shutil import get_unpack_formats, ReadError, unpack_archive
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve, HTTPError

from furl import furl
from git import GitCommandError, Repo
from path import Path

from dependen6make.exceptions import Dependen6makeError
from dependen6make.filesystem import CACHE_FETCH


ARCHIVE_EXTENSIONS = [ext for format in get_unpack_formats() for ext in format[1]]


@dataclass
class Dependency:
    """Dependency for the project."""

    name: str
    url: str
    directory_name: str = None
    url_parsed: furl = None
    git_hash: str = None
    cmake_args: str = None
    fetched: bool = False

    def __post_init__(self):
        # parse URL
        self.url_parsed = furl(self.url)

    def get_slug_name(self):
        """Get a slugified name of the dependency."""
        return "_".join(self.name.lower().split())

    def get_hash_url(self):
        """Get a hashed URL of the dependency."""
        return hashlib.md5(self.url.encode()).hexdigest()

    def get_extension(self):
        """Get extension in the URL."""
        return Path(self.url_parsed.path.segments[-1]).ext

    def get_directory_name_git(self):
        """Get directory name for a Git dependency."""
        return self.get_slug_name()

    def get_directory_name_archive(self):
        """Get directory name for an archive dependency."""
        return f"{self.get_slug_name()}_{self.get_hash_url()}"

    def refresh(self):
        """Refresh state of dependency based on attributes and cache content."""
        # get directory name based on extension
        extension = self.get_extension()
        if extension == ".git":
            self.directory_name = self.get_directory_name_git()

        elif extension in ARCHIVE_EXTENSIONS:
            self.directory_name = self.get_directory_name_archive()

        else:
            raise UnknownDependencyTypeError(
                f"Unable to manage dependency {self.name} of type {extension}"
            )

        # get fetched status based on cache
        if (CACHE_FETCH / self.directory_name).exists():
            self.fetched = True

    def describe(self, output=sys.stdout):
        """Describe dependency in text."""
        output.write(f"Name: {self.name}\n")
        output.write(f"URL: {self.url}\n")
        if self.git_hash:
            output.write(f"Git hash: {self.git_hash}\n")

        if self.cmake_args:
            output.write(f"CMake arguments: {self.cmake_args}\n")

        if self.directory_name:
            output.write(f"Directory name: {self.directory_name}\n")

        if self.fetched:
            output.write("Fetched\n")

    def fetch(self):
        """Fetch the dependency according to its type.

        Types are for now limited to Git repository or archive file.
        """
        # detect type according to extension
        extension = self.get_extension()

        if extension == ".git":
            self.fetch_git()

        elif extension in ARCHIVE_EXTENSIONS:
            self.fetch_archive()

        else:
            raise UnknownDependencyTypeError(
                f"Unable to manage dependency {self.name} of type {extension}"
            )

        # mark as fetched
        self.fetched = True

    def fetch_git(self):
        """Fetch a Git repository and checkout to the requested hash if necessary.

        Directory name is set to slugified version of dependency name.
        """
        self.directory_name = self.get_directory_name_git()
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
        """Fech an archive online and decompress it.

        Directory name is set to hashed URL of the dependency."""
        self.directory_name = self.get_directory_name_archive()
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

            # decompress file in a special directory, as we cannot list the
            # content of the archive
            decompress_path = Path(temp_directory) / "extract"
            decompress_path.mkdir_p()
            try:
                unpack_archive(archive_path, decompress_path)

            except ReadError as error:
                raise ArchiveDecompressError(
                    f"Cannot decompress archive of {self.name}: {error}"
                ) from error

            # move the decompress path
            self.move_decompress_path(decompress_path, path)

    @staticmethod
    def move_decompress_path(decompress_path: Path, destination_path: Path):
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
        to_move_path.move(destination_path)


class UnknownDependencyTypeError(Dependen6makeError):
    pass


class ArchiveDownloadError(Dependen6makeError):
    pass


class ArchiveDecompressError(Dependen6makeError):
    pass


class GitRepoFetchError(Dependen6makeError):
    pass
