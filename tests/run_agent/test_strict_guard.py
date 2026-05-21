"""
Tests for agent.strict_guard - the strict output guardrail.
"""

from __future__ import annotations

import pytest
from agent.strict_guard import (
    filter_meta_commentary,
    strict_filter,
    get_strict_mode,
    set_strict_mode,
    toggle_strict_mode,
    load_strict_config,
)


class TestStrictModeToggle:
    def test_default_is_off(self):
        set_strict_mode(False)
        assert get_strict_mode() is False

    def test_set_and_get(self):
        set_strict_mode(True)
        assert get_strict_mode() is True
        set_strict_mode(False)
        assert get_strict_mode() is False

    def test_toggle_flips_state(self):
        set_strict_mode(False)
        result = toggle_strict_mode()
        assert result is True
        result = toggle_strict_mode()
        assert result is False

    def test_load_strict_config_turns_on_when_enabled(self):
        set_strict_mode(False)
        result = load_strict_config({"display": {"strict_mode": True}})
        assert result is True
        assert get_strict_mode() is True

    def test_load_strict_config_turns_off_when_disabled(self):
        set_strict_mode(True)
        result = load_strict_config({"display": {"strict_mode": False}})
        assert result is False
        assert get_strict_mode() is False


class TestFilterMetaCommentary:
    def test_empty_string(self):
        assert filter_meta_commentary("") == ""
        assert filter_meta_commentary("   ") == ""

    def test_normal_text_passes_through(self):
        text = "Here is the final answer."
        assert filter_meta_commentary(text) == text

    def test_strips_the_user_wants(self):
        result = filter_meta_commentary("The user wants X.\nAnswer.")
        assert "The user" not in result
        assert "Answer." in result

    def test_strips_let_me_think(self):
        result = filter_meta_commentary("Let me think.\nAnswer is 42.")
        assert "Let me" not in result
        assert "Answer is 42." in result

    def test_strips_i_need_to(self):
        result = filter_meta_commentary("I need to check.\nConfig at /etc/")
        assert "I need" not in result
        assert "Config at /etc/" in result

    def test_preserves_code_and_urls(self):
        text = "Here is code:\nprint(1)"
        result = filter_meta_commentary(text)
        assert "code" in result
        assert "print(1)" in result

    def test_multiline_with_multiple_meta_patterns(self):
        text = "Let me analyze.\nThe user wants X.\nI need to check.\n\nResult: OK"
        result = filter_meta_commentary(text)
        assert "Let me" not in result
        assert "The user" not in result
        assert "I need" not in result
        assert "Result: OK" in result

    def test_case_insensitive(self):
        result = filter_meta_commentary("LET ME THINK.\nCapital Answer.")
        assert "Let me" not in result
        assert "Capital Answer." in result

    def test_let_me_know_passes_through(self):
        text = "Let me know if you have questions.\nHere is the answer."
        result = filter_meta_commentary(text)
        assert "Let me know" in result
        assert "Here is the answer." in result

    def test_all_lines_are_meta(self):
        result = filter_meta_commentary("The user wants X.\nLet me think.\nOkay")
        assert result.strip() == ""

    def test_strips_progress_note(self):
        result = filter_meta_commentary("Progress note: checking things.\nActual result.")
        assert "Progress note" not in result
        assert "Actual result." in result

    def test_strips_key_insight(self):
        result = filter_meta_commentary("Key insight: something important.\nHere is the data.")
        assert "Key insight" not in result
        assert "Here is the data." in result

    def test_strips_let_me_extended(self):
        result = filter_meta_commentary("Let me check the facts.\nFinal: 42")
        assert "Let me check" not in result
        assert "Final: 42" in result

    def test_strips_i_should_note(self):
        result = filter_meta_commentary("I should mention this nuance.\nThe answer is clear.")
        assert "I should mention" not in result
        assert "The answer is clear." in result

    def test_strips_based_on_preamble(self):
        result = filter_meta_commentary("Based on the above analysis,\n42 is the answer.")
        assert "Based on the above" not in result
        assert "42 is the answer." in result


class TestStrictFilter:
    def test_strips_think_blocks(self):
        result = strict_filter("<think>internal</think>\nHere is answer.")
        assert "<think>" not in result
        assert "internal" not in result
        assert "Here is answer." in result

    def test_strips_think_and_meta(self):
        result = strict_filter("<think>check</think>\nLet me explain.\n\n## Answer\n\nDone.")
        assert "<think>" not in result
        assert "Let me" not in result
        assert "## Answer" in result
        assert "Done." in result

    def test_empty_string(self):
        assert strict_filter("") == ""

    def test_pure_content_passes_through(self):
        text = "The answer is 42."
        result = strict_filter(text)
        assert result == text
