import contextlib
from importlib.resources import files, as_file

from path import Path


@contextlib.contextmanager
def path(module: str, name: str) -> Path:
    with as_file(files(module) / name) as file:
        yield Path(file)
