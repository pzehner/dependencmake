from subprocess import CalledProcessError, DEVNULL, PIPE, run
from typing import Optional

from path import Path

from dependen6make.exceptions import Dependen6makeError


def check_cmake_exists():
    """Check if CMake executable is available."""
    try:
        run(["cmake", "--version"], stdout=DEVNULL, stderr=DEVNULL, check=True)

    except FileNotFoundError as error:
        raise CMakeNotFoundError("CMake executable was not found") from error

    except CalledProcessError as error:
        raise CMakeNotUseableError("CMake executable cannot be run") from error


def cmake_configure(
    source_path: Path,
    build_path: Path,
    install_path: Path,
    extra_args: list = [],
    quiet: bool = True,
):
    """Configure a project with CMake."""
    command = [
        "cmake",
        f"-DCMAKE_INSTALL_PREFIX={install_path}",
        f"-DCMAKE_PREFIX_PATH={install_path}",
        *extra_args,
        "-S",
        source_path,
        "-B",
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
        "cmake",
        "--build",
        build_path,
        "--parallel",
        str(jobs),
    ]
    output = get_output(quiet)

    try:
        run(command, stdout=output, stderr=output, check=True)

    except CalledProcessError as error:
        raise CMakeBuildError(
            f"Build failed with code {error.returncode}: {error.stderr.decode()}"
        ) from error


def get_output(quiet: bool) -> Optional[int]:
    """Get output strategy based on quietness."""
    if quiet:
        return PIPE

    return None


class CMakeNotFoundError(Dependen6makeError):
    pass


class CMakeNotUseableError(Dependen6makeError):
    pass


class CMakeConfigureError(Dependen6makeError):
    pass


class CMakeBuildError(Dependen6makeError):
    pass
