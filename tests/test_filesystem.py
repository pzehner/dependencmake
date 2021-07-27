from unittest.mock import call

from path import Path

from dependencmake.filesystem import CACHE_BUILD, CACHE_FETCH, CACHE_INSTALL, clean


class TestClean:
    def test_clean(self, mocker):
        """Clean cache."""
        mocked_rmtree = mocker.patch.object(Path, "rmtree", autospec=True)

        clean(True, True, True)

        mocked_rmtree.assert_has_calls(
            [
                call(CACHE_FETCH, ignore_errors=True),
                call(CACHE_BUILD, ignore_errors=True),
                call(CACHE_INSTALL, ignore_errors=True),
            ]
        )

    def test_clean_install_path(self, mocker):
        """Clean cache with specified install path."""
        mocked_rmtree = mocker.patch.object(Path, "rmtree", autospec=True)

        clean(True, True, True, Path("lib"))

        mocked_rmtree.assert_has_calls(
            [
                call(CACHE_FETCH, ignore_errors=True),
                call(CACHE_BUILD, ignore_errors=True),
                call(Path("lib"), ignore_errors=True),
            ]
        )
