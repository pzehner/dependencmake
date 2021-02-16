from argparse import Namespace
from io import StringIO

from path import Path

from dependencmake.__main__ import get_parser, run_create_config


class TestGetParser:
    def test_get(self):
        """Get a parser."""
        parser = get_parser()
        assert parser is not None


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
