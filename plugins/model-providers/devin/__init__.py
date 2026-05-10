"""Devin autonomous coding agent provider profile.

NOTE: Devin is NOT an OpenAI-compatible LLM endpoint. It uses a session-based
API (POST /sessions, GET /sessions/{id}, POST /sessions/{id}/send-message).
This plugin registers Devin so it appears in `hermes model` and credential
resolution works, but actual inference routing requires the Devin adapter
in agent/ or delegation via subagent.
"""

from providers import register_provider
from providers.base import ProviderProfile

devin = ProviderProfile(
    name="devin",
    aliases=("devin-ai", "cognition"),
    env_vars=("DEVIN_API_KEY", "DEVIN_BASE_URL"),
    display_name="Devin (Autonomous Coding Agent)",
    description="Devin — autonomous AI software engineer by Cognition",
    signup_url="https://app.devin.ai/settings",
    fallback_models=(
        "devin-v1",
    ),
    base_url="https://api.devin.ai/v1",
    auth_type="api_key",
)

register_provider(devin)
