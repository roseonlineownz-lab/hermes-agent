from types import SimpleNamespace

from gateway.activity_labels import (
    describe_incoming_request,
    humanize_activity,
)


def test_current_tool_uses_human_friendly_label():
    assert humanize_activity({"current_tool": "execute_code"}) == "Running code"


def test_completed_tool_is_a_result_review_phase():
    assert humanize_activity(
        {
            "current_tool": None,
            "last_activity_desc": "tool completed: execute_code (20.9s)",
        }
    ) == "Running code finished (20.9s); reviewing the result"


def test_unknown_tool_name_is_not_exposed():
    assert humanize_activity({"current_tool": "private_vendor_connector"}) == (
        "Using an integration"
    )


def test_parallel_tools_are_summarized_without_names():
    assert humanize_activity({"current_tool": "terminal,web_search"}) == (
        "Running 2 steps in parallel"
    )


def test_youtube_request_is_identified_without_echoing_url():
    event = SimpleNamespace(
        text="Please review https://www.youtube.com/watch?v=secret",
        media_urls=[],
    )
    assert describe_incoming_request(event) == "YouTube link"


def test_generic_url_is_called_a_link():
    event = SimpleNamespace(text="https://example.com/private", media_urls=[])
    assert describe_incoming_request(event) == "link"
