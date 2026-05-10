# Devin Setup — hermes-agent
 
## What is this?
Fork of NousResearch/hermes-agent — a self-improving AI agent with TUI, multi-platform messaging gateway, skills system, and learning loop.
 
## Key features
- Full TUI with multiline editing, slash-commands, streaming
- Telegram, Discord, Slack, WhatsApp, Signal gateway
- Autonomous skill creation and self-improvement
- 7 terminal backends (local, Docker, SSH, Modal, Daytona, etc.)
- Provider-agnostic (OpenRouter, OpenAI, Anthropic, NVIDIA, etc.)
 
## Architecture
- Python, Click CLI
- `plugins/model-providers/` — LLM provider plugins
- `skills/` — Agent skill definitions
- `agent/` — Core agent logic
- `gateway/` — Messaging platform adapters
 
## This is a fork
Upstream: https://github.com/NousResearch/hermes-agent
Custom changes should be tracked separately from upstream syncs.
