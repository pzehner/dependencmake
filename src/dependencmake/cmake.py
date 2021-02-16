from subprocess import CalledProcessError, DEVNULL, PIPE, run
from typing import Optional

from path import Path

from dependencmake.exceptions import DependenCmakeError


CMAKE = "cmake"
CMAKE_BUILD = "--build"
CMAKE_BUILD_PATH = "-B"
CMAKE_INSTALL = "--install"
CMAKE_INSTALL_PREFIX = "-DCMAKE_INSTALL_PREFIX={}"
CMAKE_LISTS_FILE = "CMakeLists.txt"
CMAKE_PARALLEL = "--parallel"
CMAKE_PREFIX_PATH = "-DCMAKE_PREFIX_PATH={}"
CMAKE_SOURCE_PATH = "-S"
CMAKE_VERSION = "--version"


def check_cmake_exists():
    """Check if CMake executable is available."""
    try:
        run([CMAKE, CMAKE_VERSION], stdout=DEVNULL, stderr=DEVNULL, check=True)

    except FileNotFoundError as error:
        raise CMakeNotFoundError("CMake executable was not found") from error

    except CalledProcessError as error:
        raise CMakeNotUseableError("CMake executable cannot be run") from error


def check_cmake_lists_file_exists(path: Path):
    """Check if CMake lists file exists in the provided directory."""
    if not (path / CMAKE_LISTS_FILE).exists():
        raise CMakeListsFileNotFound(f"{CMAKE_LISTS_FILE} not found in {path}")


def cmake_configure(
    source_path: Path,
    build_path: Path,
    install_path: Path,
    extra_args: list = [],
    quiet: bool = True,
):
    """Configure a project with CMake."""
    command = [
        CMAKE,
        CMAKE_INSTALL_PREFIX.format(install_path),
        CMAKE_PREFIX_PATH.format(install_path),
        *extra_args,
        CMAKE_SOURCE_PATH,
        source_path,
        CMAKE_BUILD_PATH,
        build_path,
    ]
    output = get_output(quiet)

    try:
        run(command, stdout=output, stderr=output, check=True)

    except CalledProcessError as error:
        raise CMakeConfigureError(
            f"Configuration failed with code {error.returncode}: "
            f"{error.stderr.decode()}"
        ) from error


def cmake_build(
    build_path: Path,
    jobs: int,
    quiet: bool = True,
):
    """Build a project with CMake."""
    command = [
        CMAKE,
        CMAKE_BUILD,
        build_path,
        CMAKE_PARALLEL,
        str(jobs),
    ]
    output = get_output(quiet)

    try:
        run(command, stdout=output, stderr=output, check=True)

    except CalledProcessError as error:
        raise CMakeBuildError(
            f"Build failed with code {error.returncode}: {error.stderr.decode()}"
        ) from error


def cmake_install(
    build_path: Path,
    quiet: bool = True,
):
    """Install a project with CMake."""
    command = [
        CMAKE,
        CMAKE_INSTALL,
        build_path,
    ]
    output = get_output(quiet)

    try:
        run(command, stdout=output, stderr=output, check=True)

    except CalledProcessError as error:
        raise CMakeInstallError(
            f"Install failed with code {error.returncode}: {error.stderr.decode()}"
        ) from error


def get_output(quiet: bool) -> Optional[int]:
    """Get output strategy based on quietness."""
    if quiet:
        return PIPE

    return None


class CMakeNotFoundError(DependenCmakeError):
    pass


class CMakeNotUseableError(DependenCmakeError):
    pass


class CMakeListsFileNotFound(DependenCmakeError):
    pass


class CMakeConfigureError(DependenCmakeError):
    pass


class CMakeBuildError(DependenCmakeError):
    pass


class CMakeInstallError(DependenCmakeError):
    pass
