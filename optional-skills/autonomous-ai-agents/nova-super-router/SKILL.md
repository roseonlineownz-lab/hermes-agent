---
name: nova-super-router
description: "Cross-agent routing strategy for the Nova ecosystem (Mark-XXX, candy-ai-clone, NovaCockpit, NEXOR). Choose the right LLM provider per task type, delegate heavy work to other Nova agents, and fall back gracefully across Anthropic/Gemini/Ollama-pool/Kryven/OpenRouter/Groq."
version: 1.0.0
author: Hermes Agent + Kenny / NovaMaster
license: MIT
metadata:
  hermes:
    tags: [routing, multi-agent, nova, novamaster, mark-xxx, candy-ai-clone, nexor, kryven, ollama, gemini, anthropic, fallback, observability]
    related_skills: [hermes-agent, opencode, codex, claude-code]
---

# Nova Super-Router

Hermes is the connector for the Nova ecosystem. Other Nova agents — Mark-XXX (JARVIS runtime), candy-ai-clone (roleplay/voice/video), NovaCockpit (multimodal dashboard), NEXOR (orchestration), HacxGPT-CLI (uncensored CLI), Antigravity-Manager (account proxy) — each have their own strengths. Use this skill to:

1. Pick the right LLM provider for a task based on what's available, what's cheap, and what's safe.
2. Delegate work to whichever Nova agent is the best owner of that task.
3. Set up a sane fallback chain so a single provider outage never breaks the workflow.

This skill is **provider-aware**, **cost-aware**, and **failure-aware**. It does not replace Hermes's existing model resolution (`agent/auxiliary_client.py`, `agent/model_metadata.py`, `agent/error_classifier.py`) — it sits one level up, deciding *which provider chain* to hand to those.

---

## Available Providers (May 2026 snapshot)

The Nova stack has subscriptions or keys for the following providers. Order roughly by cost-per-1k-output-tokens, cheapest first.

| Provider | Endpoint | Auth | Notes |
|---|---|---|---|
| **Ollama Pool** (local) | `OLLAMA_URLS` (CSV of `http://host:11434`) | none | Two Ollama Pro subs — load-balanced via `core.ollama_pool` in Mark-XXX. Free at the margin. Use for bulk / non-latency-sensitive / private tasks. |
| **Groq** | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | Free tier + paid. Very fast. Limited model selection. |
| **Gemini Pro** | `https://generativelanguage.googleapis.com/` | `GEMINI_API_KEY` | Subscribed. 2M-token context. Good multimodal. |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | Aggregator — gives access to dozens of models incl. abliterated/uncensored variants. |
| **Kryven** (uncensored router) | `https://api.kryven.cc/v1` | `KRYVEN_API_KEY` | Conductor MoE auto-router (`kry-5.2-extended`) + 5 task-specialised variants. **Only use as one-of-many uncensored backends, never as sole provider.** |
| **Anthropic Claude** | `https://api.anthropic.com/v1` | `ANTHROPIC_API_KEY` | Subscribed. Best for long-form reasoning, code review, careful drafting. |
| **xAI Grok** | `https://api.x.ai/v1` | `XAI_API_KEY` | Pro subscription. Strong vision + video. |
| **DeepSeek** | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` | Cheap, decent code & math. |
| **NVIDIA NIM** | `https://integrate.api.nvidia.com/v1` | `NVIDIA_API_KEY` | Free tier — useful as last-resort fallback. |
| **HuggingFace Inference** | `https://api-inference.huggingface.co` | `HF_TOKEN` | Free for community models. Variable latency. |

Always read keys from env (`os.environ.get("XXX_API_KEY", "")`) — never hard-code, never log.

---

## Pick a Provider (decision tree)

The router decides on the basis of three signals: **task class**, **constraints**, and **availability**.

### Task classes

| Class | Signal | Default chain |
|---|---|---|
| `chat.fast` | short reply, latency matters, no tools | `groq → gemini → openrouter → ollama` |
| `chat.long` | multi-turn, may need tools, quality matters | `anthropic → gemini → openrouter` |
| `code.gen` | write code, no internet | `anthropic → deepseek → gemini → ollama` |
| `code.review` | reason about diff, structured output | `anthropic → gemini` |
| `reasoning.deep` | math, planning, long chain-of-thought | `anthropic → gemini → kryven/reasoning` |
| `vision` | image input | `gemini → anthropic → xai → kryven/vision` |
| `longctx` | input > 200k tokens | `gemini → kryven/longctx → anthropic` |
| `roleplay.uncensored` | candy-ai-clone style | `ollama (heretic/dolphin) → openrouter (abliterated) → kryven/auto` |
| `bulk.embed` | embeddings or massive low-stakes generation | `ollama → huggingface → nvidia` |

### Constraints that override the default

- `must_be_local: true` → `ollama` only.
- `must_be_uncensored: true` → drop Anthropic/Gemini, use `ollama (heretic/dolphin) → openrouter → kryven`.
- `max_cost_per_call_usd: <X>` → drop Anthropic if X < 0.05, drop Gemini if X < 0.01.
- `latency_p50_ms: <X>` → drop Anthropic if X < 1000, prefer Groq.
- `needs_tools: true` → drop pure-text providers, prefer Anthropic / OpenAI-compatible with function-calling.

### Availability

If `GROQ_API_KEY` is unset, drop Groq. Same for every provider. Never put a provider in the chain if its env var is empty — that wastes a round-trip and adds latency.

---

## Delegate to Other Nova Agents

Hermes is good at terminal-driven, tool-using tasks. Other Nova agents are better at specific things. Delegate by HTTP when the task is a clearer fit elsewhere.

| Task | Owner | How |
|---|---|---|
| Voice roleplay, NSFW personas, TTS, video gen | **candy-ai-clone** | `POST {CANDY_BASE_URL}/api/chat` with `persona_id` + message. Endpoints in `nova_candy_app.py`. |
| Lead generation, OSINT, browser automation, MCP-heavy ops | **Mark-XXX** | `POST {MARKXXX_BASE_URL}/api/route_chat` (cockpit) — exposes the full AgentBus. |
| Multimodal dashboards, image gen via Stability, ElevenLabs TTS | **NovaCockpit** | `POST {NOVACOCKPIT_BASE_URL}/api/chat`, `POST /api/image`, `POST /api/tts`. |
| Music generation | **NEXOR** music module | `POST {NEXOR_BASE_URL}/api/music/generate`. Suno-backed. |
| Account-rotated proxy for Anthropic/Gemini OAuth pools | **Antigravity-Manager** | Use as `ANTHROPIC_BASE_URL` / `GEMINI_BASE_URL` override — speaks OpenAI protocol. |
| Uncensored CLI with hand-tuned jailbreak prompts | **HacxGPT-CLI** | `hacxgpt --provider <X> --prompt <Y>` over SSH/local. |

Don't blindly delegate everything — the round-trip cost of HTTP + JSON-encoding adds 50–500ms. Only delegate when the other agent has *tooling* you don't, not just a different model.

---

## Reference Implementation (drop-in helper)

If you need a tiny in-process router (no LLM call, no extra deps), copy this into your tool. It implements the decision tree above against env-based availability.

```python
"""nova_super_router.py — pure-Python provider chain selector.

Usage:
    from nova_super_router import route

    chain = route(task_class="code.gen", constraints={"max_cost_per_call_usd": 0.02})
    # -> ["deepseek", "gemini", "ollama"]

No network calls. No LLM. Just env-aware filtering of pre-defined chains.
"""
from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

# Default chain per task class. Order = preference.
_DEFAULT_CHAINS: dict[str, Sequence[str]] = {
    "chat.fast":           ("groq", "gemini", "openrouter", "ollama"),
    "chat.long":           ("anthropic", "gemini", "openrouter"),
    "code.gen":            ("anthropic", "deepseek", "gemini", "ollama"),
    "code.review":         ("anthropic", "gemini"),
    "reasoning.deep":      ("anthropic", "gemini", "kryven"),
    "vision":              ("gemini", "anthropic", "xai", "kryven"),
    "longctx":             ("gemini", "kryven", "anthropic"),
    "roleplay.uncensored": ("ollama", "openrouter", "kryven"),
    "bulk.embed":          ("ollama", "huggingface", "nvidia"),
}

# Env var that gates each provider. Empty value means "unavailable".
_ENV_KEY_FOR: dict[str, str] = {
    "anthropic":   "ANTHROPIC_API_KEY",
    "gemini":      "GEMINI_API_KEY",
    "openai":      "OPENAI_API_KEY",
    "openrouter":  "OPENROUTER_API_KEY",
    "groq":        "GROQ_API_KEY",
    "deepseek":    "DEEPSEEK_API_KEY",
    "xai":         "XAI_API_KEY",
    "kryven":      "KRYVEN_API_KEY",
    "huggingface": "HF_TOKEN",
    "nvidia":      "NVIDIA_API_KEY",
    # ollama is local — gated by OLLAMA_URLS or the legacy single-URL fallback
    "ollama":      "OLLAMA_URLS",
}

# Approx output cost per 1k tokens (USD, May 2026). Used only to drop providers
# that exceed `max_cost_per_call_usd`. Keep numbers rough — don't claim precision.
_COST_PER_1K_OUT: dict[str, float] = {
    "ollama":      0.000,
    "huggingface": 0.000,
    "nvidia":      0.000,
    "groq":        0.0008,
    "deepseek":    0.001,
    "kryven":      0.002,
    "openrouter":  0.005,   # varies wildly; conservative midpoint
    "gemini":      0.005,
    "xai":         0.015,
    "anthropic":   0.015,
}


def _is_available(provider: str) -> bool:
    """True if the provider has at least one usable credential in the environment."""
    if provider == "ollama":
        # ollama is healthy if any of these is set; default localhost falls through
        for k in ("OLLAMA_URLS", "OLLAMA_BASE_URL", "OLLAMA_HOST", "MARKXXX_OLLAMA_URL"):
            if os.environ.get(k):
                return True
        return False  # don't assume localhost — caller should be explicit
    key_env = _ENV_KEY_FOR.get(provider)
    if not key_env:
        return False
    return bool(os.environ.get(key_env, "").strip())


def route(
    task_class: str,
    constraints: Mapping[str, Any] | None = None,
    *,
    extra_drop: Sequence[str] = (),
) -> list[str]:
    """Return an ordered, env-filtered provider chain for the given task class.

    Args:
        task_class:  one of ``_DEFAULT_CHAINS`` keys.
        constraints: optional dict with any of:
                       must_be_local: bool
                       must_be_uncensored: bool
                       max_cost_per_call_usd: float
                       prefer: list[str]   (move these to the front)
        extra_drop:  providers to remove unconditionally (e.g. ``("anthropic",)``).

    Returns:
        List of provider names, ordered by preference, all confirmed available.
        Empty list if nothing is reachable — caller must handle.
    """
    constraints = dict(constraints or {})
    chain = list(_DEFAULT_CHAINS.get(task_class, _DEFAULT_CHAINS["chat.long"]))

    # Hard overrides
    if constraints.get("must_be_local"):
        chain = [p for p in chain if p == "ollama"]
    if constraints.get("must_be_uncensored"):
        # drop "safety-aligned" providers; keep open-weight + jailbreak routers
        chain = [p for p in chain if p not in ("anthropic", "gemini", "openai")]

    # Cost ceiling
    cost_cap = constraints.get("max_cost_per_call_usd")
    if cost_cap is not None:
        chain = [p for p in chain if _COST_PER_1K_OUT.get(p, float("inf")) <= cost_cap]

    # Caller drops
    for p in extra_drop:
        while p in chain:
            chain.remove(p)

    # Caller preferences — only promote providers already in the filtered chain,
    # so prefer=[...] cannot revive a provider that was just dropped by a safety
    # constraint (must_be_uncensored, must_be_local, max_cost_per_call_usd, extra_drop).
    preferred = constraints.get("prefer") or []
    if preferred:
        front = [p for p in preferred if p in chain]
        chain = front + [p for p in chain if p not in front]

    # Availability filter — drop anything without creds
    chain = [p for p in chain if _is_available(p)]

    return chain
```

This file ships as **reference**; copy into a plugin or skill action when you need it. It deliberately does not call out to an LLM — picking a chain should be sub-millisecond and offline.

---

## When to Trace

When `plugins/observability/langfuse` is active, every LLM call is already traced. Add a `task_class` and `chosen_provider` tag on the active span so traces are query-able by routing decision:

```python
from langfuse import propagate_attributes  # already a hermes optional dep

with propagate_attributes(metadata={"task_class": "code.gen", "chosen_provider": "anthropic"}):
    result = run_llm_call(...)
```

In Mark-XXX use `core.observability.trace_call(...)` (added in PR #10) which wraps the same Langfuse SDK with the same metadata fields. Cross-agent traces line up in the Langfuse dashboard when both call sites set `session_id` to the user's session.

---

## Common Mistakes

- **Don't put a provider in a chain if its env var is empty.** It wastes a round-trip per call. The reference impl filters by `_is_available` for this reason.
- **Don't use Kryven as the only uncensored backend.** Always pair it with `ollama (heretic/dolphin)` and `openrouter` so a single outage doesn't take you offline. See `KRYVEN_INTEGRATION.md` in the planning docs for the validation test against Gemini-passthrough.
- **Don't delegate trivial chat to Mark-XXX or candy-ai-clone over HTTP.** A 200ms round-trip per turn destroys the conversational feel. Delegate only when the *tools* there are the differentiator.
- **Don't hard-code provider order in agent code.** Read the chain from the user's `.env` (`MARKXXX_PROVIDER_DEFAULT`, `HERMES_PROVIDER_CHAIN`) so admins can rotate priorities without a code change.

---

## Related Files

- `core/model_router.py` (Mark-XXX) — does the actual `_call_<provider>` dispatch.
- `config/model_router.py` (Mark-XXX) — `DEFAULT_PROVIDER_CHAIN` whitelist + `_openai_like_endpoint` map.
- `core/ollama_pool.py` (Mark-XXX) — local pool for the dual Ollama Pro subs.
- `agent/auxiliary_client.py` (hermes-agent) — model resolution + credential pool.
- `agent/error_classifier.py` (hermes-agent) — drives fallback when a provider 429s or 5xxs.
- `plugins/model-providers/<name>/__init__.py` — per-provider plugin profiles.
- `plugins/observability/langfuse/__init__.py` — span tagging hook used by traces above.
