from io import StringIO
from unittest.mock import call

import pytest
from path import Path

from dependen6make.dependency import Dependency
from dependen6make.dependency_list import DependencyList
from dependen6make.filesystem import CACHE, CACHE_FETCH


@pytest.fixture
def dependency_list():
    dependency_list = DependencyList()
    dependency_list.create_dependencies(
        [
            {"name": "My dep 1", "url": "http://example.com/dep1"},
            {"name": "My dep 2", "url": "http://example.com/dep2"},
        ]
    )

    return dependency_list


class TestDependencyList:
    def test_create_dependencies(self):
        """Create dependencies from list."""
        dependency_list = DependencyList()
        assert len(dependency_list.dependencies) == 0
        dependency_list.create_dependencies(
            [
                {"name": "My dep 1", "url": "http://example.com/dep1"},
                {"name": "My dep 2", "url": "http://example.com/dep2"},
            ]
        )
        assert len(dependency_list.dependencies) == 2
        assert isinstance(dependency_list.dependencies[0], Dependency)
        assert isinstance(dependency_list.dependencies[1], Dependency)

    def test_describe(self, dependency_list, mocker):
        """Describe dependencies in list."""
        mocked_refresh = mocker.patch.object(Dependency, "refresh")
        mocked_describe = mocker.patch.object(Dependency, "describe")

        output = StringIO()
        dependency_list.describe(output)

        mocked_refresh.assert_called_with()
        mocked_describe.assert_called_with(output)

    def test_fetch(self, dependency_list, mocker):
        """Fetch dependencies in list."""
        mocked_mkdir_p = mocker.patch.object(Path, "mkdir_p", autospec=True)
        mocked_fetch = mocker.patch.object(Dependency, "fetch")

        output = StringIO()
        dependency_list.fetch(output)

        mocked_mkdir_p.assert_has_calls([call(CACHE), call(CACHE_FETCH)])
        mocked_fetch.assert_called_with()
