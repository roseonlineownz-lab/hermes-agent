---
name: daily-morning-briefing
description: Automated morning briefing via Telegram — service health, GPU status, disk space, recent leads, and overnight errors. Fires once daily. Uses NovaMaster health checks + Telegram delivery.
category: automation
tags: [telegram, health-check, briefing, cron, monitoring]
---

# Daily Morning Briefing

Triggers: user asks for "morning briefing", "daily report", "status update", or cron fires each morning.

## What It Does

1. Runs layered health diagnostics on the NovaMaster stack
2. Checks GPU temperature, VRAM, utilization
3. Checks disk space on /home and /mnt/c
4. Tails overnight error logs from ~/.hermes/logs/errors.log
5. Scans Docker containers for exited/non-running
6. Compiles into a compact Telegram message
7. Delivers to the configured Telegram chat

## Implementation

This skill is designed to be deployed as a cron job via Hermes:

```
cronjob create \
  name="Morning Briefing" \
  schedule="0 8 * * *" \
  prompt="Run the NovaMaster morning briefing: run health diagnostics, check GPU/disk/errors, summarize into Dutch Telegram message. Be concise. Use nova-health-diagnostics skill." \
  skills=["nova-health-diagnostics"] \
  deliver="telegram"
```

## Manual Trigger

From any Hermes session:
```
Run the morning briefing now.
```

## Checklist

- [ ] Service health (nova status or layered diagnostics)
- [ ] Docker container states
- [ ] GPU: temp, VRAM, utilization (nvidia-smi)
- [ ] Disk: df -h /home /mnt/c
- [ ] Memory: free -h
- [ ] Load: uptime
- [ ] Error log tail (last 20 lines from ~/.hermes/logs/errors.log)
- [ ] Any DOWN services flagged with priority (P0/P1/P2)

## Message Format (Dutch, Compact)

```
☤ NovaMaster Ochtendbriefing — [Datum]

📊 SERVICES
  UP: X/Y — [list any DOWN services]

🎮 GPU
  RTX 5070 Ti — [temp]°C — [VRAM used]/[total]

💾 OPSLAG
  /home: [gebruikt]% — /mnt/c: [gebruikt]%

⚠️ FOUTEN (afgelopen 24u)
  [samenvatting of "Geen kritieke fouten"]

🔱 Empire status: [OPERATIONEEL/AANDACHT NODIG]
```

## Pitfalls

- Telegram delivery may fail if gateway is down — fall back to local terminal output
- Some services report DOWN in health scripts but are actually UP (port mismatch, WSL bridge issues) — always cross-check with `docker ps` and `systemctl --user status`
- If GPU is at 95°C+, flag as CRITICAL and suggest investigation
- Disk over 85%: flag, over 95%: CRITICAL with cleanup suggestion
