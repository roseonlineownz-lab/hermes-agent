---
name: nova-automation-pack
description: Pre-built automations for NovaMaster — health checks, trend scans, daily briefings
schedule: daily
---

# NovaMaster Automation Pack

## 1. Daily Health Check (8am)
**Prompt Hermes:**
"Check all NovaMaster services: hermes-gateway, litellm-proxy, clawmem-serve, metaclaw, goclaw, comfyui, ollama. Report status. If any service is down, try to fix it and report back."

## 2. AI Trend Scanner (9am)
**Prompt Hermes:**
"Use Firecrawl to scan these sources for the latest AI news (since yesterday):
- r/MachineLearning on Reddit
- Hacker News frontpage
- GitHub trending Python repos
Create a 5-point briefing with: headline, why it matters, and if we can use it in NovaMaster.
Save to /home/faramix/.hermes/daily-briefings/$(date +%Y-%m-%d).md"

## 3. Social Media Auto-Poster (10am, 2pm, 6pm)
**Prompt Hermes:**
"Find 1 interesting AI/tech story. Draft a tweet about it (under 280 chars). Generate an image hint for ComfyUI. Ask me for approval before posting."

## 4. GitHub Repo Monitor (every 3 hours)
**Prompt Hermes:**
"Check these GitHub repos for new releases: claude-code, hermes-agent, openclaw, comfyui, litellm. If any new release in last 24h, summarize changelog and flag if we should update."

## 5. Evening Wrap-up (8pm)
**Prompt Hermes:**
"Summarize today: what automations ran, any errors, what you learned, and 1 improvement for tomorrow. Save to /home/faramix/.hermes/daily-briefings/wrap-$(date +%Y-%m-%d).md"

---

# How to Schedule These
In Hermes TUI or Telegram:
- `/cron add "0 8 * * *" daily-health-check` — Health check elke dag 8am
- `/cron add "0 9 * * *" ai-trend-scanner` — Trend scan elke dag 9am
- `/cron add "0 10,14,18 * * *" social-auto-poster` — Posts 3x per dag
- `/cron add "0 */3 * * *" github-monitor` — GitHub check elke 3 uur
- `/cron add "0 20 * * *" evening-wrapup` — Wrap-up elke dag 8pm
