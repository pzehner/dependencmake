from pathlib import Path as Pathlib

import pytest
from path import Path

from dependencmake.config import (
    ConfigNotFoundError,
    IncorrectConfigError,
    check_config,
    create_config,
    get_config,
)


class TestCreateConfig:
    def test_create(self, mocker):
        """Create a config file in empty directory."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_copy = mocker.patch.object(Path, "copy", autospec=True)
        mocked_path = mocker.patch("dependencmake.config.path", autospec=True)
        mocked_path.return_value.__enter__.return_value = (
            Pathlib("resources") / "dependencmake.yaml"
        )

        create_config(Path("path"))

        mocked_exists.assert_called_with(Path("path") / "dependencmake.yaml")
        mocked_path.assert_called()
        mocked_copy.assert_called_with(
            Path("resources") / "dependencmake.yaml",
            Path("path") / "dependencmake.yaml",
        )

    def test_create_exists_overwrite(self, mocker):
        """Overwrite a config file."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_copy = mocker.patch.object(Path, "copy", autospec=True)
        mocked_path = mocker.patch("dependencmake.config.path", autospec=True)
        mocked_path.return_value.__enter__.return_value = (
            Pathlib("resources") / "dependencmake.yaml"
        )
        mocked_input = mocker.patch("dependencmake.config.input")
        mocked_input.return_value = "yes"

        create_config(Path("path"))

        mocked_copy.assert_called_with(
            Path("resources") / "dependencmake.yaml",
            Path("path") / "dependencmake.yaml",
        )

    def test_create_exists_no_overwrite(self, mocker):
        """Don't overwrite a config file."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_copy = mocker.patch.object(Path, "copy", autospec=True)
        mocked_path = mocker.patch("dependencmake.config.path", autospec=True)
        mocked_path.return_value.__enter__.return_value = (
            Pathlib("resources") / "dependencmake.yaml"
        )
        mocked_input = mocker.patch("dependencmake.config.input")
        mocked_input.return_value = "no"

        create_config(Path("path"))

        mocked_copy.assert_not_called()

    def test_create_exists_force(self, mocker):
        """Force overwrite a config file."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_copy = mocker.patch.object(Path, "copy", autospec=True)
        mocked_path = mocker.patch("dependencmake.config.path", autospec=True)
        mocked_path.return_value.__enter__.return_value = (
            Pathlib("resources") / "dependencmake.yaml"
        )

        create_config(Path("path"), True)

        mocked_copy.assert_called_with(
            Path("resources") / "dependencmake.yaml",
            Path("path") / "dependencmake.yaml",
        )


class TestGetConfig:
    def test_get(self, mocker):
        """Get a normal config."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = True
        mocked_text = mocker.patch.object(Path, "read_text", autospec=True)
        mocked_text.return_value = "config: value"

        config = get_config(Path("path"))
        assert config == {"config": "value"}

        mocked_exists.assert_called_with(Path("path") / "dependencmake.yaml")
        mocked_text.assert_called_with(Path("path") / "dependencmake.yaml")

    def test_not_found(self, mocker):
        """Error when getting not found config."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_text = mocker.patch.object(Path, "read_text", autospec=True)

        with pytest.raises(ConfigNotFoundError):
            get_config(Path("path"))

        mocked_exists.assert_called_with(Path("path") / "dependencmake.yaml")
        mocked_text.assert_not_called()


class TestCheckConfig:
    def test_check(self):
        """Check a valid config."""
        check_config({"dependencies": []})

    def test_no_dependencies(self):
        """Check a config without dependencies list."""
        with pytest.raises(IncorrectConfigError):
            check_config({})
