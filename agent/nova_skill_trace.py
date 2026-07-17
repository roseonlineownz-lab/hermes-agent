"""Native, best-effort Hermes adapter for Nova Skill Trace events.

The adapter keeps only ephemeral lifecycle state. Its emitted CLI arguments
come from a closed allowlist and never include tool/LLM payloads, paths,
environment values, or credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import uuid
from typing import Any, Callable


CLI_PATH = Path("/home/faramix/bin/nova-skill-trace")
CLI_PATH_FALLBACK = Path("/home/faramix/work/NovaMaster/bin/nova-skill-trace")
CLI_TIMEOUT_SECONDS = 0.5
_CANONICAL_SKILL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@+-]{0,95}$")
_SOURCES = frozenset({"skill_view", "preload", "bundle", "skill_command"})
_SKILL_TOOLS = frozenset({"skill_view", "skills_list"})


@dataclass
class _Trace:
    skill: str
    source: str
    trace_id: str
    task_id: str | None = None
    session_id: str | None = None
    turn_id: str | None = None
    used: bool = False
    failed: bool = False


def _opaque_id(kind: str, value: object | None) -> str | None:
    if value is None or value == "":
        return None
    digest = hashlib.sha256(str(value).encode("utf-8", errors="replace")).hexdigest()[:24]
    return f"hermes-{kind}-{digest}"


class SkillTraceAdapter:
    """Track native skill lifecycle state and emit privacy-bounded evidence."""

    def __init__(self, cli_path: Path = CLI_PATH) -> None:
        self._cli_paths = (
            (cli_path, CLI_PATH_FALLBACK)
            if cli_path == CLI_PATH
            else (cli_path,)
        )
        self._lock = threading.RLock()
        self._traces: list[_Trace] = []

    def _available(self) -> Path | None:
        try:
            return next(
                (
                    path
                    for path in self._cli_paths
                    if os.path.isfile(path) and os.access(path, os.X_OK)
                ),
                None,
            )
        except Exception:
            return None

    def _emit(self, trace: _Trace, phase: str, status: str) -> None:
        try:
            cli_path = self._available()
            if cli_path is None:
                return
            cli = str(cli_path)
            argv = [
                cli,
                "emit",
                "--provider",
                "hermes",
                "--phase",
                phase,
                "--skill",
                trace.skill,
                "--reason",
                f"source={trace.source} status={status}",
                "--evidence",
                "native_hook",
                "--trace-id",
                trace.trace_id,
            ]
            session_id = _opaque_id("session", trace.session_id)
            turn_id = _opaque_id("turn", trace.turn_id)
            if session_id:
                argv.extend(("--session-id", session_id))
            if turn_id:
                argv.extend(("--turn-id", turn_id))
            subprocess.run(  # noqa: S603 -- fixed executable and allowlisted argv
                argv,
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=CLI_TIMEOUT_SECONDS,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            )
        except Exception:
            # Skill tracing is observability only and must never affect Hermes.
            return

    @staticmethod
    def _matches(
        trace: _Trace,
        *,
        task_id: object | None,
        session_id: object | None,
        turn_id: object | None,
    ) -> bool:
        if trace.task_id and task_id and trace.task_id != str(task_id):
            return False
        if trace.session_id and session_id and trace.session_id != str(session_id):
            return False
        if trace.turn_id and turn_id and trace.turn_id != str(turn_id):
            return False
        return bool(
            (trace.task_id and task_id)
            or (trace.session_id and session_id)
            or (trace.turn_id and turn_id)
            or not (trace.task_id or trace.session_id or trace.turn_id)
        )

    @staticmethod
    def _bind(
        trace: _Trace,
        *,
        task_id: object | None,
        session_id: object | None,
        turn_id: object | None,
    ) -> None:
        if task_id is not None and task_id != "":
            trace.task_id = str(task_id)
        if session_id is not None and session_id != "":
            trace.session_id = str(session_id)
        if turn_id is not None and turn_id != "":
            trace.turn_id = str(turn_id)

    def record_loaded(
        self,
        skill: str,
        *,
        source: str,
        task_id: object | None = None,
        session_id: object | None = None,
        turn_id: object | None = None,
    ) -> None:
        """Record one successful native load using its canonical skill name."""
        if (
            not self._available()
            or source not in _SOURCES
            or not isinstance(skill, str)
            or not _CANONICAL_SKILL.fullmatch(skill)
        ):
            return
        trace = _Trace(
            skill=skill,
            source=source,
            trace_id=f"hermes-trace-{uuid.uuid4().hex}",
            task_id=str(task_id) if task_id not in (None, "") else None,
            session_id=str(session_id) if session_id not in (None, "") else None,
            turn_id=str(turn_id) if turn_id not in (None, "") else None,
        )
        with self._lock:
            self._traces.append(trace)
        self._emit(trace, "matched", "matched")
        self._emit(trace, "loaded", "completed")

    def pre_tool_call(self, *, tool_name: str = "", **kwargs: Any) -> None:
        if tool_name in _SKILL_TOOLS:
            return
        to_emit: list[_Trace] = []
        context = {
            "task_id": kwargs.get("task_id"),
            "session_id": kwargs.get("session_id"),
            "turn_id": kwargs.get("turn_id"),
        }
        with self._lock:
            for trace in self._traces:
                if trace.used or not self._matches(trace, **context):
                    continue
                self._bind(trace, **context)
                trace.used = True
                to_emit.append(trace)
        for trace in to_emit:
            self._emit(trace, "used", "started")

    def post_tool_call(
        self, *, tool_name: str = "", status: str = "ok", **kwargs: Any
    ) -> None:
        context = {
            "task_id": kwargs.get("task_id"),
            "session_id": kwargs.get("session_id"),
            "turn_id": kwargs.get("turn_id"),
        }
        if tool_name == "skill_view":
            if status not in {"ok", "success", "completed"}:
                return
            try:
                result = kwargs.get("result")
                parsed = json.loads(result) if isinstance(result, str) else result
                if not isinstance(parsed, dict) or not parsed.get("success"):
                    return
                canonical = parsed.get("name")
                if not isinstance(canonical, str):
                    return
            except Exception:
                return
            self.record_loaded(canonical, source="skill_view", **context)
            return
        if tool_name in _SKILL_TOOLS or status in {"ok", "success", "completed"}:
            return
        with self._lock:
            for trace in self._traces:
                if trace.used and self._matches(trace, **context):
                    trace.failed = True

    def post_llm_call(self, **kwargs: Any) -> None:
        context = {
            "task_id": kwargs.get("task_id"),
            "session_id": kwargs.get("session_id"),
            "turn_id": kwargs.get("turn_id"),
        }
        completed: list[_Trace] = []
        with self._lock:
            remaining: list[_Trace] = []
            for trace in self._traces:
                if self._matches(trace, **context):
                    self._bind(trace, **context)
                    completed.append(trace)
                else:
                    remaining.append(trace)
            self._traces = remaining
        for trace in completed:
            status = "failed" if trace.failed else "completed" if trace.used else "partial"
            self._emit(trace, "receipt", status)

    def on_session_end(self, **kwargs: Any) -> None:
        """Discard unreceipted turn state; receipts are post-LLM evidence only."""
        context = {
            "task_id": kwargs.get("task_id"),
            "session_id": kwargs.get("session_id"),
            "turn_id": kwargs.get("turn_id"),
        }
        with self._lock:
            self._traces = [
                trace for trace in self._traces if not self._matches(trace, **context)
            ]

    def hook_callbacks(self) -> dict[str, Callable[..., None]]:
        return {
            "pre_tool_call": self.pre_tool_call,
            "post_tool_call": self.post_tool_call,
            "post_llm_call": self.post_llm_call,
            "on_session_end": self.on_session_end,
        }


_ADAPTER = SkillTraceAdapter()


def record_loaded(skill: str, *, source: str, task_id: object | None = None) -> None:
    """Fail-open entry point for native preload and bundle paths."""
    try:
        _ADAPTER.record_loaded(skill, source=source, task_id=task_id)
    except Exception:
        return


def native_hook_callbacks() -> dict[str, Callable[..., None]]:
    return _ADAPTER.hook_callbacks()
