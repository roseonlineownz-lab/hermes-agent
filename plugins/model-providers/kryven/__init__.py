"""Kryven provider profile.

Kryven (https://api.kryven.cc/v1) exposes an OpenAI-compatible /v1 endpoint
backed by the Conductor MoE router (Qwen3-class open weights). Treat it as one
of multiple uncensored backends — never as the sole route. The picker should
keep Dolphin/Heretic, OpenRouter abliterated, and Ollama-local options
available as primary fallbacks.
"""

from providers import register_provider
from providers.base import ProviderProfile

kryven = ProviderProfile(
    name="kryven",
    aliases=("kry", "kryven.cc"),
    env_vars=("KRYVEN_API_KEY",),
    display_name="Kryven",
    description="Kryven Conductor — uncensored MoE router (OpenAI-compatible)",
    signup_url="https://www.kryven.cc/",
    base_url="https://api.kryven.cc/v1",
    fallback_models=(
        "kry-5.2-extended",
        "kry-5.2-code",
        "kry-5.2-reasoning",
        "kry-5.2-vision",
        "kry-5.2-longctx",
        "kry-5.2-fast",
    ),
)

register_provider(kryven)
