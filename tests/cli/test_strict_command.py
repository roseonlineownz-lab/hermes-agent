"""Tests for the CLI /strict command and strict-mode config wiring."""

from unittest.mock import MagicMock, patch

from cli import HermesCLI
from hermes_cli.commands import resolve_command


def _make_cli():
    cli_obj = HermesCLI.__new__(HermesCLI)
    cli_obj.config = {}
    cli_obj.console = MagicMock()
    cli_obj.agent = None
    cli_obj.conversation_history = []
    cli_obj.session_id = None
    cli_obj._pending_input = MagicMock()
    cli_obj._console_print = MagicMock()
    cli_obj._toggle_yolo = MagicMock()
    return cli_obj


def test_strict_command_is_available_in_registry():
    cmd = resolve_command("strict")
    assert cmd is not None
    assert cmd.category == "Configuration"
    assert "clean" in cmd.aliases


def test_process_command_strict_toggles_and_persists():
    cli_obj = _make_cli()

    with (
        patch("cli.toggle_strict_mode", return_value=True) as mock_toggle,
        patch("cli.save_config_value", return_value=True) as mock_save,
    ):
        assert cli_obj.process_command("/strict") is True

    mock_toggle.assert_called_once_with()
    mock_save.assert_called_once_with("display.strict_mode", True)
    printed = " ".join(str(call.args[0]) for call in cli_obj._console_print.call_args_list)
    assert "Strict output mode: ON" in printed
    assert "(saved)" in printed


def test_process_command_clean_alias_dispatches_to_strict():
    cli_obj = _make_cli()

    with (
        patch("cli.toggle_strict_mode", return_value=False) as mock_toggle,
        patch("cli.save_config_value", return_value=False) as mock_save,
    ):
        assert cli_obj.process_command("/clean") is True

    mock_toggle.assert_called_once_with()
    mock_save.assert_called_once_with("display.strict_mode", False)
    printed = " ".join(str(call.args[0]) for call in cli_obj._console_print.call_args_list)
    assert "Strict output mode: OFF" in printed
    assert "(session only)" in printed


def test_process_command_yolo_does_not_touch_strict_config():
    cli_obj = _make_cli()

    with patch("cli.save_config_value") as mock_save:
        assert cli_obj.process_command("/yolo") is True

    cli_obj._toggle_yolo.assert_called_once_with()
    mock_save.assert_not_called()
