"""Context-aware slash-command recommendations for the interactive CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BuddyState:
    """Small, serializable snapshot of CLI state used for recommendations."""

    agent_running: bool = False
    busy_input_mode: str = "interrupt"
    goal_active: bool = False
    pending_count: int = 0
    background_count: int = 0
    session_tokens: int = 0
    tool_progress: str = ""
    yolo_enabled: bool = False


@dataclass(frozen=True)
class BuddyRecommendation:
    """One CLI command recommendation with a short reason."""

    command: str
    reason: str
    topics: tuple[str, ...]


def _add_unique(
    items: list[BuddyRecommendation],
    command: str,
    reason: str,
    *topics: str,
) -> None:
    if any(item.command == command for item in items):
        return
    items.append(BuddyRecommendation(command, reason, tuple(topics)))


def recommend_cli_commands(
    state: BuddyState,
    *,
    topic: str | None = None,
    limit: int = 8,
) -> list[BuddyRecommendation]:
    """Return practical next slash commands for the current CLI state."""

    normalized_topic = (topic or "").strip().lower()
    mode = (state.busy_input_mode or "interrupt").strip().lower()
    recs: list[BuddyRecommendation] = []

    if state.goal_active:
        _add_unique(recs, "/goal status", "Check the active standing goal.", "goal", "run")
        _add_unique(recs, "/goal pause", "Pause auto-continue before changing direction.", "goal", "run")

    if state.agent_running:
        _add_unique(
            recs,
            "/steer <note>",
            "Nudge the running agent after its next tool call without interrupting it.",
            "busy",
            "run",
        )
        if mode != "steer":
            _add_unique(
                recs,
                "/busy steer",
                "Make future mid-run Enter messages steer instead of interrupt.",
                "busy",
                "config",
            )
        _add_unique(recs, "/queue <prompt>", "Line up the next turn without breaking the current one.", "busy", "run")
        _add_unique(recs, "/agents", "See active agents and background work.", "run", "status")
    else:
        _add_unique(recs, "/goal <outcome>", "Let Hermes keep working across turns until the outcome is reached.", "goal", "run")
        _add_unique(recs, "/background <prompt>", "Start a separate task while keeping this session free.", "background", "run")
        _add_unique(recs, "/model", "Inspect or switch the current model before a hard task.", "model", "config")

    if state.pending_count > 0:
        _add_unique(recs, "/queue <prompt>", "There is already queued work; add follow-up work intentionally.", "busy", "run")

    if state.background_count > 0:
        _add_unique(recs, "/agents", "Track running background tasks.", "background", "status")

    if state.session_tokens >= 100_000:
        _add_unique(recs, "/usage", "Check token pressure before the context gets too expensive.", "context", "status")
        _add_unique(recs, "/compress <focus>", "Compress the session around the part you still need.", "context")
    else:
        _add_unique(recs, "/usage", "Check tokens, calls, and provider limits.", "context", "status")
        _add_unique(recs, "/compress <focus>", "Compress around a topic when the session gets noisy.", "context")

    if state.tool_progress == "verbose":
        _add_unique(recs, "/verbose", "Cycle tool output if the terminal is too noisy.", "display", "config")
    else:
        _add_unique(recs, "/verbose", "Show more tool detail when debugging.", "display", "config")

    _add_unique(recs, "/tools list", "Inspect enabled tools before assigning work.", "tools", "status")
    _add_unique(recs, "/skills browse", "Find a task-specific skill instead of hand-rolling a workflow.", "skills", "tools")
    _add_unique(recs, "/snapshot create <label>", "Checkpoint state before risky changes.", "safety", "config")

    if state.yolo_enabled:
        _add_unique(recs, "/yolo", "Turn approval bypass off before broad or destructive work.", "safety", "config")

    if normalized_topic:
        aliases = {
            "stuck": {"busy", "run", "status"},
            "interrupt": {"busy", "config"},
            "context": {"context"},
            "model": {"model", "config"},
            "tools": {"tools", "skills", "status"},
            "safe": {"safety", "config"},
            "goal": {"goal", "run"},
            "background": {"background", "run"},
        }
        wanted = aliases.get(normalized_topic, {normalized_topic})
        recs = [rec for rec in recs if wanted.intersection(rec.topics)]

    return recs[: max(1, limit)]
