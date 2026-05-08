---
name: ollama-model-monitor
description: Monitors Ollama cloud model availability, tracks token costs via LiteLLM, alerts on model failures or cost spikes. Keeps the model arsenal healthy.
category: automation
tags: [ollama, litellm, monitoring, models, cost-tracking]
---

# Ollama Model Health & Cost Monitor

Triggers: user asks "which models are up?", "model status", "check ollama", or cron fires every 6 hours.

## What It Does

1. Probes Ollama API (:11434/api/tags) for local model availability
2. Probes LiteLLM (:4000/v1/models) for routing status
3. Tests each cloud model with a lightweight inference call (single-token test)
4. Tracks estimated token costs based on known pricing
5. Alerts via Telegram when a model goes down or returns errors
6. Maintains a model health log at ~/.hermes/data/models/health.json

## Cloud Model Pricing (per 1M tokens, May 2026)

| Model | Input | Output |
|-------|-------|--------|
| deepseek-v4-pro | $1.74 | $3.48 |
| deepseek-v4-flash | $0.55 | $1.10 |
| deepseek-v3.2 | $0.27 | $1.10 |
| minimax-m2.5 | $0.40 | $1.60 |
| minimax-m2.7 | $0.50 | $2.00 |
| glm-5 | $1.20 | $4.80 |
| glm-4.6 | $0.80 | $3.20 |
| kimi-k2.5 | $0.60 | $2.40 |
| qwen3.5 | $0.35 | $1.40 |
| gemma4 | $0.15 | $0.60 |
| nemotron-3-super | $2.00 | $8.00 |
| gpt-oss | $0.50 | $2.00 |

## Usage

### Health Check
```
check all models
ollama model status
welke modellen werken?
```

### Cost Report
```
model cost report
wat kost mijn model usage deze maand?
litellm spending summary
```

### Alert Setup (cron)
```
cronjob create \
  name="Model Health Check" \
  schedule="0 */6 * * *" \
  prompt="Run ollama model health check: probe all cloud models via LiteLLM, test with single-token inference, report any failures or slow responses (>5s)." \
  skills=["ollama-model-monitor"]
```

## Test Payload

```json
{
  "model": "deepseek-v4-pro",
  "messages": [{"role": "user", "content": "."}],
  "max_tokens": 1,
  "temperature": 0
}
```

Route through LiteLLM (:4000) to test the full path: Ollama → LiteLLM → Cloud API.

## Alert Thresholds

- **CRITICAL**: Model returns 4xx/5xx for 3 consecutive checks
- **WARNING**: Response time > 5 seconds (model degraded)
- **WARNING**: Model missing from /api/tags but was present last check
- **INFO**: New model detected in /api/tags

## Health Log Format

```json
{
  "last_check": "2026-05-08T08:00:00Z",
  "models": {
    "deepseek-v4-pro": {
      "status": "healthy",
      "latency_ms": 1200,
      "last_error": null,
      "consecutive_failures": 0
    }
  }
}
```

## Pitfalls

- Ollama cloud models may be "present" in /api/tags but fail on actual inference (API key expired, provider down)
- Single-token tests still consume a tiny amount of credits — negligible but cumulative
- LiteLLM routing may hide underlying provider failures — test direct Ollama too
- Some cloud models have cold-start latency (first call slow, subsequent calls fast)
- The pricing table must be updated when providers change rates
