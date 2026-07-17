"""Focused contract tests for Hermes' native Nova Skill Trace adapter."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def _argv_fields(argv: list[str]) -> dict[str, str]:
    assert argv[1] == "emit"
    return dict(zip(argv[2::2], argv[3::2]))


@pytest.fixture
def emitted(monkeypatch):
    from agent import nova_skill_trace

    calls: list[tuple[list[str], dict]] = []
    monkeypatch.setattr(nova_skill_trace.os.path, "isfile", lambda _path: True)
    monkeypatch.setattr(nova_skill_trace.os, "access", lambda _path, _mode: True)

    def fake_run(argv, **kwargs):
        calls.append((list(argv), kwargs))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(nova_skill_trace.subprocess, "run", fake_run)
    return calls


def test_ordering_exactly_once_used_and_redacted_argv(emitted):
    from agent.nova_skill_trace import SkillTraceAdapter

    adapter = SkillTraceAdapter()
    adapter.record_loaded(
        "canonical-skill",
        source="preload",
        task_id="task secret /home/operator prompt",
    )
    adapter.pre_tool_call(
        tool_name="terminal",
        task_id="task secret /home/operator prompt",
        session_id="session with secret",
        turn_id="turn with secret",
        args={"command": "cat /home/operator/token"},
    )
    adapter.pre_tool_call(
        tool_name="browser",
        task_id="task secret /home/operator prompt",
        session_id="session with secret",
        turn_id="turn with secret",
        args={"url": "https://secret.invalid"},
    )
    adapter.post_llm_call(
        task_id="task secret /home/operator prompt",
        session_id="session with secret",
        turn_id="turn with secret",
        user_message="private prompt",
        assistant_response="private response",
    )

    fields = [_argv_fields(argv) for argv, _ in emitted]
    assert [item["--phase"] for item in fields] == [
        "matched",
        "loaded",
        "used",
        "receipt",
    ]
    assert {item["--trace-id"] for item in fields} == {fields[0]["--trace-id"]}
    assert all(item["--provider"] == "hermes" for item in fields)
    assert all(item["--skill"] == "canonical-skill" for item in fields)
    assert fields[-1]["--reason"] == "source=preload status=completed"

    rendered = json.dumps(emitted)
    for secret in (
        "private prompt",
        "private response",
        "cat /home/operator/token",
        "https://secret.invalid",
        "session with secret",
        "turn with secret",
        "task secret /home/operator prompt",
    ):
        assert secret not in rendered

    allowed = {
        "--provider",
        "--phase",
        "--skill",
        "--reason",
        "--evidence",
        "--trace-id",
        "--session-id",
        "--turn-id",
    }
    assert all(set(argv[2::2]) <= allowed for argv, _ in emitted)
    assert all(kwargs["timeout"] == 0.5 for _, kwargs in emitted)
    assert all(kwargs["env"] == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"} for _, kwargs in emitted)


def test_multiple_skills_are_used_once_and_receipted(emitted):
    from agent.nova_skill_trace import SkillTraceAdapter

    adapter = SkillTraceAdapter()
    adapter.record_loaded("alpha", source="preload", task_id="task-1")
    adapter.record_loaded("beta", source="bundle", task_id="task-1")
    adapter.pre_tool_call(
        tool_name="skill_view",
        task_id="task-1",
        session_id="session-1",
        turn_id="turn-1",
    )
    adapter.pre_tool_call(
        tool_name="terminal",
        task_id="task-1",
        session_id="session-1",
        turn_id="turn-1",
    )
    adapter.pre_tool_call(
        tool_name="browser",
        task_id="task-1",
        session_id="session-1",
        turn_id="turn-1",
    )
    adapter.post_llm_call(task_id="task-1", session_id="session-1", turn_id="turn-1")

    fields = [_argv_fields(argv) for argv, _ in emitted]
    assert [(item["--skill"], item["--phase"]) for item in fields] == [
        ("alpha", "matched"),
        ("alpha", "loaded"),
        ("beta", "matched"),
        ("beta", "loaded"),
        ("alpha", "used"),
        ("beta", "used"),
        ("alpha", "receipt"),
        ("beta", "receipt"),
    ]


@pytest.mark.parametrize(
    ("mark_failed", "expected"),
    [(False, "partial"), (True, "failed")],
)
def test_receipt_partial_and_failed_status(emitted, mark_failed, expected):
    from agent.nova_skill_trace import SkillTraceAdapter

    adapter = SkillTraceAdapter()
    adapter.record_loaded("alpha", source="preload", task_id="task-1")
    if mark_failed:
        adapter.pre_tool_call(
            tool_name="terminal",
            task_id="task-1",
            session_id="session-1",
            turn_id="turn-1",
        )
        adapter.post_tool_call(
            tool_name="terminal",
            status="error",
            task_id="task-1",
            session_id="session-1",
            turn_id="turn-1",
            result={"error": "secret failure detail"},
        )
    adapter.post_llm_call(task_id="task-1", session_id="session-1", turn_id="turn-1")

    receipt = _argv_fields(emitted[-1][0])
    assert receipt["--phase"] == "receipt"
    assert receipt["--reason"] == f"source=preload status={expected}"
    assert "secret failure detail" not in json.dumps(emitted)


def test_skill_view_uses_canonical_success_name_only(emitted):
    from agent.nova_skill_trace import SkillTraceAdapter

    adapter = SkillTraceAdapter()
    adapter.post_tool_call(
        tool_name="skill_view",
        status="ok",
        task_id="task-1",
        session_id="session-1",
        turn_id="turn-1",
        args={"name": "alias-with-private-context"},
        result=json.dumps(
            {
                "success": True,
                "name": "plugin:canonical",
                "content": "private skill instructions",
                "path": "/home/operator/private/SKILL.md",
            }
        ),
    )

    fields = [_argv_fields(argv) for argv, _ in emitted]
    assert [item["--phase"] for item in fields] == ["matched", "loaded"]
    assert all(item["--skill"] == "plugin:canonical" for item in fields)
    rendered = json.dumps(emitted)
    assert "alias-with-private-context" not in rendered
    assert "private skill instructions" not in rendered
    assert "/home/operator/private" not in rendered

    adapter.post_tool_call(
        tool_name="skill_view",
        status="error",
        result={"success": False, "name": "must-not-load"},
    )
    assert len(emitted) == 2


def test_missing_cli_and_timeout_are_fail_open(monkeypatch):
    from agent import nova_skill_trace

    adapter = nova_skill_trace.SkillTraceAdapter(cli_path=Path("/missing/nova-skill-trace"))
    called = False

    def should_not_run(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess should not run")

    monkeypatch.setattr(nova_skill_trace.subprocess, "run", should_not_run)
    adapter.record_loaded("alpha", source="preload")
    assert called is False
    assert adapter._traces == []

    monkeypatch.setattr(nova_skill_trace.os.path, "isfile", lambda _path: True)
    monkeypatch.setattr(nova_skill_trace.os, "access", lambda _path, _mode: False)
    adapter.record_loaded("alpha", source="preload")
    assert called is False
    assert adapter._traces == []

    monkeypatch.setattr(nova_skill_trace.os, "access", lambda _path, _mode: True)

    def time_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("nova-skill-trace", 0.1)

    monkeypatch.setattr(nova_skill_trace.subprocess, "run", time_out)
    adapter.record_loaded("beta", source="bundle")  # must not raise


def test_native_callback_registration_and_session_cleanup(emitted):
    from agent.nova_skill_trace import SkillTraceAdapter
    from hermes_cli.plugins import PluginManager

    manager = PluginManager()
    assert set(manager._native_hooks) == {
        "pre_tool_call",
        "post_tool_call",
        "post_llm_call",
        "on_session_end",
    }
    assert all(manager.has_hook(name) for name in manager._native_hooks)

    adapter = SkillTraceAdapter()
    adapter.record_loaded("alpha", source="preload", task_id="task-1")
    adapter.on_session_end(task_id="task-1", session_id="session-1", turn_id="turn-1")
    adapter.post_llm_call(task_id="task-1", session_id="session-1", turn_id="turn-1")
    assert [_argv_fields(argv)["--phase"] for argv, _ in emitted] == [
        "matched",
        "loaded",
    ]


def test_preload_and_bundle_report_only_successful_canonical_loads(monkeypatch):
    from agent import nova_skill_trace, skill_bundles, skill_commands

    recorded: list[tuple[str, str, str | None]] = []
    monkeypatch.setattr(
        nova_skill_trace,
        "record_loaded",
        lambda skill, *, source, task_id=None: recorded.append((skill, source, task_id)),
    )
    monkeypatch.setattr(skill_commands, "_build_skill_message", lambda *_a, **_kw: "body")
    monkeypatch.setattr(
        skill_commands,
        "_load_skill_payload",
        lambda identifier, task_id=None: (
            ({"name": "canonical-preload"}, Path("/tmp/skill"), "canonical-preload")
            if identifier == "preload-alias"
            else None
        ),
    )
    prompt, loaded, missing = skill_commands.build_preloaded_skills_prompt(
        ["preload-alias", "missing"], task_id="task-1"
    )
    assert prompt
    assert loaded == ["canonical-preload"]
    assert missing == ["missing"]

    monkeypatch.setattr(
        skill_bundles,
        "get_skill_bundles",
        lambda: {
            "bundle": {"name": "bundle", "skills": ["bundle-alias", "missing"]}
        },
    )
    monkeypatch.setattr(
        skill_commands,
        "_load_skill_payload",
        lambda identifier, task_id=None: (
            ({"name": "canonical-bundle"}, Path("/tmp/skill"), "canonical-bundle")
            if identifier == "bundle-alias"
            else None
        ),
    )
    message, bundle_loaded, bundle_missing = skill_bundles.build_bundle_invocation_message(
        "bundle", task_id="task-2"
    )
    assert message
    assert bundle_loaded == ["canonical-bundle"]
    assert bundle_missing == ["missing"]
    assert recorded == [
        ("canonical-preload", "preload", "task-1"),
        ("canonical-bundle", "bundle", "task-2"),
    ]
