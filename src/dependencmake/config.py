from distutils.util import strtobool

try:
    from importlib.resources import path

except ImportError:
    from importlib_resources import path  # type: ignore

from path import Path
from yaml import Loader, load

from dependencmake.exceptions import DependenCmakeError

CONFIG_NAME = "dependencmake.yaml"


def create_config(directory: Path, force: bool = False):
    """Create a new config file.

    If config file already exists and not in force mode, ask for overwrite.
    """
    destination = directory / CONFIG_NAME
    if destination.exists() and not force:
        overwrite_str = input(f"{CONFIG_NAME} exists, overwrite? (yes/no) ")
        if not (overwrite_str and strtobool(overwrite_str)):
            return

    with path("dependencmake.resources", CONFIG_NAME) as resource:
        Path(resource).copy(destination)


def get_config(path: Path) -> dict:
    """Read config file."""
    config_path = path / CONFIG_NAME
    if not config_path.exists():
        raise ConfigNotFoundError(f"Unable to find a {CONFIG_NAME} file in {path}")

    return load(config_path.read_text(), Loader=Loader)


def check_config(config: dict):
    """Check if the config file is valid."""
    if "dependencies" not in config:
        raise IncorrectConfigError("Key 'dependencies' missing from config")


class ConfigNotFoundError(DependenCmakeError):
    pass


class IncorrectConfigError(DependenCmakeError):
    pass
