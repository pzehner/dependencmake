import pytest
from path import Path

from dependen6make.config import (
    check_config,
    ConfigNotFoundError,
    get_config,
    IncorrectConfigError,
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

        mocked_exists.assert_called_with(Path("path") / "dependen6make.yaml")
        mocked_text.assert_called_with(Path("path") / "dependen6make.yaml")

    def test_not_found(self, mocker):
        """Error when getting not found config."""
        mocked_exists = mocker.patch.object(Path, "exists", autospec=True)
        mocked_exists.return_value = False
        mocked_text = mocker.patch.object(Path, "read_text", autospec=True)

        with pytest.raises(ConfigNotFoundError):
            get_config(Path("path"))

        mocked_exists.assert_called_with(Path("path") / "dependen6make.yaml")
        mocked_text.assert_not_called()


class TestCheckConfig:
    def test_check(self):
        """Check a valid config."""
        check_config({"dependencies": []})

    def test_no_dependencies(self):
        """Check a config without dependencies list."""
        with pytest.raises(IncorrectConfigError):
            check_config({})
