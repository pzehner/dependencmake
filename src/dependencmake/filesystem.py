from path import Path

CACHE = Path("dependencmake")
CACHE_FETCH = CACHE / "fetch"
CACHE_BUILD = CACHE / "build"
CACHE_INSTALL = CACHE / "install"


def clean(fetch: bool = False, build: bool = False, install: bool = False):
    """Clean cache directories."""
    if fetch:
        CACHE_FETCH.rmtree(ignore_errors=True)

    if build:
        CACHE_BUILD.rmtree(ignore_errors=True)

    if install:
        CACHE_INSTALL.rmtree(ignore_errors=True)
