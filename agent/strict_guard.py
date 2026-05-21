"""
Strict output guardrail for Hermes Agent CLI/TUI.

Filters visible thinking, meta-commentary, and inner monologue patterns
from final assistant output. Designed to be wired into:
- agent/conversation_loop.py (assistant content print)
- run_agent.py _fire_stream_delta (streaming output)
"""

from __future__ import annotations

import re
from typing import List, Tuple
import logging

# ---------------------------------------------------------------------------
# Global strict-mode toggle (per-process; set by /strict slash command)
# ---------------------------------------------------------------------------
_strict_mode: bool = False


def get_strict_mode() -> bool:
    """Return current strict-mode state."""
    return _strict_mode


def set_strict_mode(enabled: bool) -> None:
    """Set strict-mode state."""
    global _strict_mode
    _strict_mode = enabled


def toggle_strict_mode() -> bool:
    """Toggle and return new strict-mode state."""
    global _strict_mode
    _strict_mode = not _strict_mode
    return _strict_mode


# ---------------------------------------------------------------------------
# Meta-commentary patterns
# ---------------------------------------------------------------------------

# Line-level patterns: anchored with ^...$ and applied with re.MULTILINE (no DOTALL).
# These patterns match a single logical line of meta-commentary.
LINE_PATTERNS: List[Tuple[str, str, str]] = [
    # Full-line meta openings
    (
        r"^The user (?:wants|is (?:asking|instructing)|has (?:asked|requested|said)|needs|expects|would like)\b.*$",
        "",
        "the-user-preamble",
    ),
    (
        r"^Let me (?:think|break|analyze|consider|check|explain|first|see|look|start|understand|try|figure|reason|walk|parse|examine|review|assess)\b.*$",
        "",
        "let-me-preamble",
    ),
    (r"^I (?:need|should|will|must|can|want|have) to\b.*$", "", "i-need-to-preamble"),
    (r"^Okay[,;:]?\s*$", "", "okay-alone"),
    (r"^Now[,;:]?\s*$", "", "now-alone"),
    (r"^First[,;:]?\s*$", "", "first-alone"),
    # Meta-analysis markers
    (r"^Analysis:.*$", "", "analysis-header"),
    (r"^Key (?:points?|findings?|takeaways?|insights?):.*$", "", "key-points-header"),
    # Progress/note meta-markers
    (r"^Progress note:.*$", "", "progress-note"),
    (r"^Key insight:.*$", "", "key-insight"),
    (r"^Let me (?:check|note|summarize|add|clarify|elaborate|restate|rephrase|confirm|verify|double[-. ]check|make sure)\b.*$", "", "let-me-extended"),
    (r"^I should (?:note|mention|add|point out|clarify|explain)\b.*$", "", "i-should-note"),
    (r"^Based on the (?:above|context|conversation|history|analysis|information|code|files|results)\b.*$", "", "based-on-preamble"),
    # Standalone XML tags left over from StreamingThinkScrubber
    (r"^</?(?:think(?:ing)?|reasoning|thought|REASONING_SCRATCHPAD)>\s*$", "", "standalone-xml-tag"),
]

# Block-level patterns: these can span multiple lines, so use re.DOTALL.
BLOCK_PATTERNS: List[Tuple[str, str, str]] = [
    # XML think/reasoning/thought blocks that escape StreamingThinkScrubber
    (r"<think(?:ing)?>.*?</think(?:ing)?>", "", "xml-think-block"),
    (r"<reasoning>.*?</reasoning>", "", "xml-reasoning-block"),
    (r"<thought>.*?</thought>", "", "xml-thought-block"),
    (r"<REASONING_SCRATCHPAD>.*?</REASONING_SCRATCHPAD>", "", "xml-scratchpad-block"),
]


def load_strict_config(config=None):
    """Load strict mode setting from config at startup."""
    enabled = False
    if config is None:
        try:
            from hermes_cli.config import load_config
            cfg = load_config()
            enabled = bool(cfg.get("display", {}).get("strict_mode", False))
        except Exception:
            pass
    else:
        enabled = bool(config.get("display", {}).get("strict_mode", False))
    if enabled:
        set_strict_mode(True)
    return get_strict_mode()


def _compile_patterns():
    """Lazily compile regex patterns."""
    if not hasattr(_compile_patterns, "_line_regexes"):
        _compile_patterns._line_regexes = [
            (re.compile(pat, re.MULTILINE | re.IGNORECASE), repl, desc)
            for pat, repl, desc in LINE_PATTERNS
        ]
        _compile_patterns._block_regexes = [
            (re.compile(pat, re.MULTILINE | re.IGNORECASE | re.DOTALL), repl, desc)
            for pat, repl, desc in BLOCK_PATTERNS
        ]
    return _compile_patterns._line_regexes, _compile_patterns._block_regexes


def filter_meta_commentary(text: str) -> str:
    """Remove meta-commentary patterns from text.

    Applies line-level and block-level regex patterns in order.
    Returns cleaned text with normalized whitespace.
    """
    if not text or not text.strip():
        return text

    line_regexes, block_regexes = _compile_patterns()

    # Apply block patterns first (they can span multiple lines)
    for regex, repl, _desc in block_regexes:
        text = regex.sub(repl, text)

    # Apply line patterns
    for regex, repl, _desc in line_regexes:
        text = regex.sub(repl, text)

    # Clean up: collapse multiple blank lines, strip leading/trailing whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n")



def strict_filter(text: str) -> str:
    """Full strict output pipeline.

    1. Runs through StreamingThinkScrubber for stateful XML tag handling.
    2. Applies meta-commentary regex filter.

    Use this for complete (non-streaming) assistant messages.
    For streaming, use filter_meta_commentary() after the existing think scrubber.
    """
    if not text or not text.strip():
        return text

    # Step 1: Use StreamingThinkScrubber to handle nested/incomplete XML tags
    try:
        from agent.think_scrubber import StreamingThinkScrubber

        scrubber = StreamingThinkScrubber()
        scrubber.feed(text)
        text = scrubber.flush()
    except Exception:
        # Defensive: if scrubber fails, fall through to regex-only
        pass

    # Step 2: Apply meta-commentary filter
    return filter_meta_commentary(text)
