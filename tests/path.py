import contextlib
from importlib.resources import as_file, files
from typing import Iterator

from path import Path


@contextlib.contextmanager
def path(module: str, name: str) -> Iterator[Path]:
    with as_file(files(module) / name) as file:
        yield Path(file)
