from path import Path
from yaml import load, Loader

from dependen6make.exceptions import Dependen6makeError


CONFIG_NAME = "dependen6make.yaml"


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


class ConfigNotFoundError(Dependen6makeError):
    pass


class IncorrectConfigError(Dependen6makeError):
    pass
