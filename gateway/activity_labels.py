"""Human-friendly labels for gateway activity and inbound requests.

The agent core intentionally tracks exact tool names for diagnostics.  Chat
surfaces should not expose those implementation details by default, though:
``tool completed: execute_code`` is meaningful to a developer but reads like
an error to most users.  These helpers translate the small amount of state the
gateway already has into stable, privacy-friendly status copy.
"""

from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import urlparse


_URL_RE = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)
_TOOL_COMPLETED_RE = re.compile(
    r"^tool completed:\s*([a-zA-Z0-9_.:-]+)(?:\s*\(([^)]+)\))?$",
    re.IGNORECASE,
)

_TOOL_ACTIVITY_LABELS: dict[str, str] = {
    "browser_click": "Interacting with the page",
    "browser_navigate": "Opening the page",
    "browser_type": "Entering information",
    "clarify": "Preparing a question",
    "cronjob": "Updating the schedule",
    "delegate_task": "Coordinating another agent",
    "execute_code": "Running code",
    "image_generate": "Creating an image",
    "memory": "Updating memory",
    "patch": "Editing files",
    "read_file": "Reading files",
    "search_files": "Searching files",
    "session_search": "Searching past sessions",
    "skill_manage": "Updating a skill",
    "skill_view": "Reading a skill",
    "terminal": "Running a command",
    "text_to_speech": "Creating audio",
    "todo": "Updating the task plan",
    "video_generate": "Creating a video",
    "vision_analyze": "Inspecting an image",
    "web_extract": "Reading a web page",
    "web_search": "Searching the web",
    "write_file": "Writing files",
}


def _tool_activity_label(tool_name: Any) -> str:
    """Return a safe activity label without leaking custom integration names."""
    raw = str(tool_name or "").strip()
    if not raw:
        return ""

    names = [name.strip() for name in raw.split(",") if name.strip()]
    labels = [_TOOL_ACTIVITY_LABELS.get(name) for name in names]
    known = [label for label in labels if label]
    if len(names) > 1:
        return f"Running {len(names)} steps in parallel"
    if known:
        return known[0]
    return "Using an integration"


def humanize_activity(summary: Mapping[str, Any] | None) -> str:
    """Describe the agent's current phase using user-facing language."""
    if not isinstance(summary, Mapping):
        return ""

    current_tool = summary.get("current_tool")
    if current_tool:
        return _tool_activity_label(current_tool)

    last_desc = str(summary.get("last_activity_desc") or "").strip()
    completed = _TOOL_COMPLETED_RE.match(last_desc)
    if completed:
        tool_label = _tool_activity_label(completed.group(1))
        duration = str(completed.group(2) or "").strip()
        detail = f" ({duration})" if duration else ""
        if tool_label:
            return f"{tool_label} finished{detail}; reviewing the result"
        return f"Step finished{detail}; reviewing the result"

    normalized = last_desc.lower()
    if normalized in {"api", "api call", "waiting for api", "calling model"}:
        return "Waiting for the model"
    if "compress" in normalized:
        return "Summarizing conversation context"
    if "reason" in normalized or "think" in normalized:
        return "Reviewing the next step"
    if "start" in normalized or "initial" in normalized:
        return "Starting the task"
    if last_desc:
        return "Reviewing the next step"
    return ""


def _first_url(text: str) -> str:
    match = _URL_RE.search(text or "")
    return match.group(0).rstrip(".,!?;:") if match else ""


def describe_incoming_request(event: Any) -> str:
    """Return a short noun phrase for a busy-session acknowledgement."""
    text = str(getattr(event, "text", "") or "")
    url = _first_url(text)
    if url:
        try:
            hostname = (urlparse(url).hostname or "").lower()
        except ValueError:
            hostname = ""
        if hostname in {"youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com"}:
            return "YouTube link"
        return "link"

    media_urls = getattr(event, "media_urls", None) or []
    if media_urls:
        media_type = str(getattr(event, "message_type", "") or "").lower()
        if "audio" in media_type or "voice" in media_type:
            return "voice message"
        if "image" in media_type or "photo" in media_type:
            return "image"
        if "video" in media_type:
            return "video"
        return "attachment"

    return "message"
