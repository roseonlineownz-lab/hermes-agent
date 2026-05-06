"""Tests for the /buddy command recommendation helper."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cli import HermesCLI
from hermes_cli.command_buddy import BuddyState, recommend_cli_commands
from hermes_cli.commands import resolve_command


def _make_cli(**overrides):
    cli_obj = HermesCLI.__new__(HermesCLI)
    cli_obj.config = {"display": {"tool_progress": "verbose"}}
    cli_obj.console = MagicMock()
    cli_obj.agent = None
    cli_obj._agent_running = False
    cli_obj.busy_input_mode = "interrupt"
    cli_obj._pending_input = SimpleNamespace(qsize=lambda: 0)
    cli_obj._background_tasks = {}
    cli_obj._goal_manager = None
    for key, value in overrides.items():
        setattr(cli_obj, key, value)
    return cli_obj


def test_buddy_command_is_registered():
    cmd = resolve_command("buddy")

    assert cmd is not None
    assert cmd.cli_only is True
    assert cmd.category == "Info"


def test_running_agent_recommends_steer_and_busy_steer():
    recs = recommend_cli_commands(
        BuddyState(agent_running=True, busy_input_mode="interrupt")
    )
    commands = [rec.command for rec in recs]

    assert "/steer <note>" in commands
    assert "/busy steer" in commands
    assert "/queue <prompt>" in commands
    assert commands.index("/steer <note>") < commands.index("/queue <prompt>")


def test_idle_agent_recommends_goal_background_and_model_commands():
    recs = recommend_cli_commands(BuddyState(agent_running=False))
    commands = [rec.command for rec in recs]

    assert "/goal <outcome>" in commands
    assert "/background <prompt>" in commands
    assert "/model" in commands


def test_goal_state_recommends_goal_controls_first():
    recs = recommend_cli_commands(
        BuddyState(agent_running=True, busy_input_mode="steer", goal_active=True)
    )
    commands = [rec.command for rec in recs]

    assert commands[:2] == ["/goal status", "/goal pause"]


def test_high_context_recommends_usage_and_compress():
    recs = recommend_cli_commands(
        BuddyState(agent_running=False, session_tokens=130_000)
    )
    commands = [rec.command for rec in recs]

    assert "/usage" in commands
    assert "/compress <focus>" in commands


def test_process_command_buddy_dispatches_handler():
    cli_obj = _make_cli()

    with patch.object(cli_obj, "_handle_buddy_command") as mock_buddy:
        assert cli_obj.process_command("/buddy busy") is True

    mock_buddy.assert_called_once_with("/buddy busy")


def test_handle_buddy_command_prints_recommendations():
    cli_obj = _make_cli(_agent_running=True)

    with patch("cli._cprint") as mock_cprint:
        cli_obj._handle_buddy_command("/buddy")

    printed = "\n".join(str(call.args[0]) for call in mock_cprint.call_args_list)
    assert "Hermes Buddy" in printed
    assert "/steer <note>" in printed
    assert "/busy steer" in printed


def test_handle_buddy_command_filters_topic():
    cli_obj = _make_cli(_agent_running=True, busy_input_mode="steer")

    with patch("cli._cprint") as mock_cprint:
        cli_obj._handle_buddy_command("/buddy context")

    printed = "\n".join(str(call.args[0]) for call in mock_cprint.call_args_list)
    assert "/usage" in printed
    assert "/compress <focus>" in printed
    assert "/steer <note>" not in printed
