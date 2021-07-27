from path import Path

CACHE = Path("dependencmake")
CACHE_FETCH = CACHE / "fetch"
CACHE_BUILD = CACHE / "build"
CACHE_INSTALL = CACHE / "install"


def clean(
    fetch: bool = False,
    build: bool = False,
    install: bool = False,
    install_path: Path = None,
):
    """Clean cache directories."""
    if fetch:
        CACHE_FETCH.rmtree(ignore_errors=True)

    if build:
        CACHE_BUILD.rmtree(ignore_errors=True)

    if install:
        install_path = install_path or CACHE_INSTALL
        install_path.rmtree(ignore_errors=True)
