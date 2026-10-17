"""Durable run approval presence is scoped to its live observed SSE stream."""
import asyncio
import os
from types import SimpleNamespace

import pytest

from gateway.platforms import api_server_runs
from tools import approval as approval_mod
from tools import approval_context

RUN_ID = "run_observer_contract"


@pytest.fixture
def approval_environment(monkeypatch):
    for name in ("HERMES_EXEC_ASK", "HERMES_INTERACTIVE", "HERMES_GATEWAY_SESSION",
                 "HERMES_CRON_SESSION", "HERMES_SINGLE_QUERY_SESSION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "api_server")
    monkeypatch.setattr(approval_context, "_session_env", lambda name: os.getenv(name, ""))
    monkeypatch.setattr(approval_context, "_get_approval_mode", lambda: "manual")
    monkeypatch.setattr(approval_context, "_get_unattended_approval_mode", lambda: "deny")
    monkeypatch.setattr(approval_mod, "_YOLO_MODE_FROZEN", False)
    token = approval_context.set_current_session_key(RUN_ID)
    approval_mod._session_approved.pop(RUN_ID, None)
    yield
    approval_mod.unregister_gateway_notify(RUN_ID)
    approval_context.reset_current_session_key(token)


async def make_run():
    stream = api_server_runs._RunStream()
    owner = SimpleNamespace(_run_streams={RUN_ID: stream},
                            _run_approval_sessions={RUN_ID: RUN_ID},
                            _stopping_run_ids=set(), _run_statuses={RUN_ID: {"status": "running"}})
    def set_status(run_id, status, **fields):
        owner._run_statuses[run_id] = {"status": status, **fields}
    owner._set_run_status = set_status
    run = SimpleNamespace(run_id=RUN_ID, queue=stream, approval_session_key=RUN_ID)
    api = SimpleNamespace(_approval_request_event=lambda run_id, data: {
        **data, "run_id": run_id, "event": "approval.request", "choices": ["once", "deny"]})
    notify = api_server_runs._make_approval_notify(owner, run, _api_server=api)
    return owner, stream, notify


def test_no_callback_and_generic_callback_are_unattended(approval_environment):
    assert approval_context._is_gateway_approval_context() is False
    approval_mod.register_gateway_notify(RUN_ID, lambda _: None)
    assert approval_context._is_gateway_approval_context() is False
    assert approval_mod._presence()[2:] == (False, False)


def test_no_callback_real_tool_gate_denies(approval_environment):
    result = approval_mod.request_tool_approval("observer-contract", "harmless test action")
    assert result["approved"] is False


@pytest.mark.parametrize("retirement", ["stream_terminal", "stop_marker", "changed_owner", "unregistered"])
def test_retired_observer_cannot_answer_new_approvals(approval_environment, retirement):
    async def exercise():
        owner, stream, notify = await make_run()
        stream.attach()
        approval_mod.register_gateway_notify(RUN_ID, notify)
        assert approval_context._is_gateway_approval_context() is True
        if retirement == "stream_terminal":
            stream.terminal = True
        elif retirement == "stop_marker":
            owner._stopping_run_ids.add(RUN_ID)
        elif retirement == "changed_owner":
            owner._run_approval_sessions[RUN_ID] = "another-session"
        else:
            approval_mod.unregister_gateway_notify(RUN_ID)
        assert approval_context._is_gateway_approval_context() is False
    asyncio.run(exercise())


def test_other_approval_session_cannot_use_observer(approval_environment):
    async def exercise():
        _, stream, notify = await make_run()
        stream.attach()
        approval_mod.register_gateway_notify(RUN_ID, notify)
        token = approval_context.set_current_session_key("another-run")
        try:
            assert approval_context._is_gateway_approval_context() is False
        finally:
            approval_context.reset_current_session_key(token)
    asyncio.run(exercise())


def test_live_subscriber_scope_and_retirement(approval_environment):
    async def exercise():
        owner, stream, notify = await make_run()
        approval_mod.register_gateway_notify(RUN_ID, notify)
        assert approval_context._is_gateway_approval_context() is False
        queue, _ = stream.attach()
        assert approval_context._is_gateway_approval_context() is True
        stream.detach(queue)
        assert approval_context._is_gateway_approval_context() is False
        stream.attach()
        owner._run_streams[RUN_ID] = api_server_runs._RunStream()
        assert approval_context._is_gateway_approval_context() is False
        owner._run_streams[RUN_ID] = stream
        owner._run_approval_sessions.pop(RUN_ID)
        assert approval_context._is_gateway_approval_context() is False
    asyncio.run(exercise())


@pytest.mark.parametrize("state", ["stopping", "completed", "failed", "cancelled", "interrupted"])
def test_terminal_or_stopping_run_has_no_presence(approval_environment, state):
    async def exercise():
        owner, stream, notify = await make_run()
        stream.attach()
        owner._run_statuses[RUN_ID]["status"] = state
        approval_mod.register_gateway_notify(RUN_ID, notify)
        assert approval_context._is_gateway_approval_context() is False
    asyncio.run(exercise())


@pytest.mark.parametrize("platform", ["webhook", "msgraph_webhook"])
def test_webhook_with_observer_callback_stays_unattended(approval_environment, monkeypatch, platform):
    async def exercise():
        _, stream, notify = await make_run()
        stream.attach()
        approval_mod.register_gateway_notify(RUN_ID, notify)
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", platform)
        assert approval_context._is_gateway_approval_context() is False
        assert approval_mod._presence()[2:] == (False, False)
    asyncio.run(exercise())


@pytest.mark.parametrize("marker", ["HERMES_CRON_SESSION", "HERMES_SINGLE_QUERY_SESSION"])
def test_cron_and_single_query_stay_unattended(approval_environment, monkeypatch, marker):
    async def exercise():
        _, stream, notify = await make_run()
        stream.attach()
        approval_mod.register_gateway_notify(RUN_ID, notify)
        monkeypatch.setenv(marker, "1")
        assert approval_context._is_gateway_approval_context() is False
        assert approval_mod._presence()[1:] == (False, False, False)
    asyncio.run(exercise())


def test_observer_probe_exception_fails_closed(approval_environment):
    def notify(_):
        pass
    def broken():
        raise RuntimeError("stream gone")
    notify._hermes_run_observer_present = broken
    approval_mod.register_gateway_notify(RUN_ID, notify)
    assert approval_context._is_gateway_approval_context() is False


@pytest.mark.parametrize("decision", ["once", "deny"])
def test_real_gate_waits_for_exact_one_request(approval_environment, decision):
    async def exercise():
        _owner, stream, notify = await make_run()
        queue, _ = stream.attach()
        approval_mod.register_gateway_notify(RUN_ID, notify)
        task = asyncio.create_task(asyncio.to_thread(
            approval_mod.request_tool_approval, "observer-contract", "harmless test action"))
        _, data = await asyncio.wait_for(queue.get(), timeout=5)
        assert data["event"] == "approval.request"
        request_id = data["request_id"]
        assert approval_mod.resolve_gateway_approval(RUN_ID, decision, request_id=request_id) == 1
        result = await asyncio.wait_for(task, timeout=5)
        assert result["approved"] is (decision == "once")
        assert "observer-contract" not in approval_mod._session_approved.get(RUN_ID, set())
    asyncio.run(exercise())
