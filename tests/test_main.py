from argparse import Namespace
from io import StringIO

from path import Path

from dependencmake.__main__ import (
    get_parser,
    run_build,
    run_clean,
    run_create_config,
    run_fetch,
    run_install,
)


class TestGetParser:
    def test_get(self):
        """Get a parser."""
        parser = get_parser()
        assert parser is not None


class TestRunFetch:
    def test_run_force(self, mocker):
        """Run the force fetch command."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean")
        mocked_dependency_list_class = mocker.patch(
            "dependencmake.__main__.DependencyList"
        )

        args = Namespace(path=Path("path"), force=True)
        output = StringIO()
        run_fetch(args, output)

        mocked_clean.assert_called_with(fetch=True)
        mocked_dependency_list_class.assert_called()


class TestRunBuild:
    def test_run_force(self, mocker):
        """Run the force build command."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean")
        mocked_dependency_list_class = mocker.patch(
            "dependencmake.__main__.DependencyList"
        )

        args = Namespace(path=Path("path"), force=True, install_path=None, rest=[])
        output = StringIO()
        run_build(args, output)

        mocked_clean.assert_called_with(fetch=True, build=True)
        mocked_dependency_list_class.assert_called()

    def test_run_extra(self, mocker):
        """Run the build command with CMake arguments."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean")
        mocked_dependency_list_class = mocker.patch(
            "dependencmake.__main__.DependencyList"
        )

        args = Namespace(
            path=Path("path"), force=False, install_path=None, rest=["-DCMAKE_ARG=ON"]
        )
        output = StringIO()
        run_build(args, output)

        mocked_clean.assert_not_called()
        mocked_dependency_list_class.return_value.build.assert_called_with(
            ["-DCMAKE_ARG=ON"], output
        )


class TestRunInstall:
    def test_run_force(self, mocker):
        """Run the force install command."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean")
        mocked_dependency_list_class = mocker.patch(
            "dependencmake.__main__.DependencyList"
        )

        args = Namespace(path=Path("path"), force=True, install_path=None, rest=[])
        output = StringIO()
        run_install(args, output)

        mocked_clean.assert_called_with(fetch=True, build=True, install=True)
        mocked_dependency_list_class.assert_called()

    def test_run_extra(self, mocker):
        """Run the install command with CMake arguments."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean")
        mocked_dependency_list_class = mocker.patch(
            "dependencmake.__main__.DependencyList"
        )

        args = Namespace(
            path=Path("path"), force=False, install_path=None, rest=["-DCMAKE_ARG=ON"]
        )
        output = StringIO()
        run_install(args, output)

        mocked_clean.assert_not_called()
        mocked_dependency_list_class.return_value.build.assert_called_with(
            ["-DCMAKE_ARG=ON"], output
        )


class TestRunCreateConfig:
    def test_run(self, mocker):
        """Run the create-config command."""
        mocked_create_config = mocker.patch(
            "dependencmake.__main__.create_config", autospec=True
        )

        args = Namespace(path=Path("path"), force=True)
        output = StringIO()
        run_create_config(args, output)

        content = output.getvalue()
        assert "Config file created in dependencmake.yaml" in content

        mocked_create_config.assert_called_with(Path("path"), True)


class TestRunClean:
    def test_run_no_args(self, mocker):
        """Run clean command without arguments."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean", autospec=True)

        args = Namespace(
            fetch=False, build=False, install=False, all=False, install_path=None
        )
        output = StringIO()
        run_clean(args, output)

        mocked_clean.assert_called_with(
            fetch=False, build=True, install=False, install_path=None
        )

    def test_run_fetch(self, mocker):
        """Run clean command with fetch argument."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean", autospec=True)

        args = Namespace(
            fetch=True, build=False, install=False, all=False, install_path=None
        )
        output = StringIO()
        run_clean(args, output)

        mocked_clean.assert_called_with(
            fetch=True, build=False, install=False, install_path=None
        )

    def test_run_build(self, mocker):
        """Run clean command with build argument."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean", autospec=True)

        args = Namespace(
            fetch=False, build=True, install=False, all=False, install_path=None
        )
        output = StringIO()
        run_clean(args, output)

        mocked_clean.assert_called_with(
            fetch=False, build=True, install=False, install_path=None
        )

    def test_run_install(self, mocker):
        """Run clean command with install argument."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean", autospec=True)

        args = Namespace(
            fetch=False, build=False, install=True, all=False, install_path=None
        )
        output = StringIO()
        run_clean(args, output)

        mocked_clean.assert_called_with(
            fetch=False, build=False, install=True, install_path=None
        )

    def test_run_all(self, mocker):
        """Run clean command with all argument."""
        mocked_clean = mocker.patch("dependencmake.__main__.clean", autospec=True)

        args = Namespace(
            fetch=False, build=False, install=False, all=True, install_path=None
        )
        output = StringIO()
        run_clean(args, output)

        mocked_clean.assert_called_with(
            fetch=True, build=True, install=True, install_path=None
        )
