# NovaMaster Automation Blueprint

Last updated: 2026-05-08

## Active Automation Skills

| Skill | Trigger | Delivery | Status |
|-------|---------|----------|--------|
| daily-morning-briefing | Cron 08:00 / manual | Telegram | Ready |
| firecrawl-lead-intel | Telegram / CLI / n8n webhook | Telegram + n8n | Ready |
| ollama-model-monitor | Cron elke 6u / manual | Telegram | Ready |
| comfyui-telegram-trigger | Telegram / CLI | Telegram | Ready |
| infra-nightly-digest | Cron 22:00 / manual | Telegram | Ready |
| browser-use-dispatcher | Telegram / CLI / cron | Telegram | Ready |
| nova-health-diagnostics | Manual / cron | Terminal / Telegram | Existing |
| novamaster-video-factory | CLI / queue | Local filesystem | Existing |

## Priority Implementation Order

1. daily-morning-briefing — highest daily value, simplest to deploy
2. infra-nightly-digest — covers the blind spots between morning checks
3. firecrawl-lead-intel — core revenue engine
4. ollama-model-monitor — keeps the AI arsenal healthy
5. comfyui-telegram-trigger — creative pipeline mobile access
6. browser-use-dispatcher — complex but high-utility for monitoring

## Integration Map

```
Telegram Bot
    ├── /morning → daily-morning-briefing
    ├── /nightly → infra-nightly-digest
    ├── /leadgen → firecrawl-lead-intel
    ├── /gen → comfyui-telegram-trigger
    ├── /browse → browser-use-dispatcher
    ├── /models → ollama-model-monitor
    └── /status → nova-health-diagnostics

n8n ↔ firecrawl-lead-intel (webhook push/pull)
LiteLLM :4000 ↔ ollama-model-monitor (routing health)
ComfyUI :8188 ↔ comfyui-telegram-trigger (prompt API)
Prometheus :9090 ↔ infra-nightly-digest (metrics)
Loki :3100 ↔ infra-nightly-digest (logs)
Space Agent :3003 ↔ browser-use-dispatcher (headless browser)
```

## Next Automation Ideas (Backlog)

- n8n → Hermes auto-triage: n8n detects an event, Hermes decides action
- Firecrawl competitor monitor: scrape competitor sites weekly, AI-diff changes
- Ollama model benchmark runner: monthly benchmark of all models, trend report
- Telegram → Obsidian note capture: forward messages to Obsidian vault
- Smart disk cleaner: AI decides which logs/caches to prune based on usage patterns
