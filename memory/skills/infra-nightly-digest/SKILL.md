---
name: infra-nightly-digest
description: Nightly infrastructure digest — compiles the day's metrics, errors, uptime, and anomalies. Delivers to Telegram. Uses Prometheus, Loki, and docker stats.
category: automation
tags: [monitoring, prometheus, loki, docker, nightly, telegram]
---

# Infrastructure Nightly Digest

Triggers: fires nightly at 22:00 or manually via "nightly digest", "infra summary", "dagelijkse status".

## What It Does

1. Pulls 24h metrics from Prometheus (:9090)
2. Queries Loki (:3100) for error/warning log patterns
3. Summarizes Docker container restarts and resource usage
4. Checks Uptime Kuma (:3002) for external monitoring data
5. Flags anomalies: unusual CPU spikes, memory leaks, disk growth
6. Compiles a compact Dutch digest to Telegram

## Metrics Collected

### From Prometheus
- CPU utilization (node, per-container)
- Memory usage trend (24h min/max/avg)
- Disk I/O and growth rate
- Network throughput
- HTTP request rates and error ratios (per service)
- GPU metrics if exported

### From Loki
- ERROR and CRITICAL log lines (count + top patterns)
- New error types not seen in previous 7 days
- Service crash/restart events
- Authentication failures

### From Docker
- Container restart count (24h)
- Containers with non-zero exit codes
- Resource hogs (top 5 by CPU, top 5 by memory)
- Image pull/update events

### From Uptime Kuma
- External reachability (Hostinger VPS, public endpoints)
- SSL certificate expiry warnings
- Latency trends

## Usage

### Manual
```
nightly digest
infra summary vandaag
wat gebeurde er vannacht met de servers?
```

### Cron Setup
```
cronjob create \
  name="Nightly Infra Digest" \
  schedule="0 22 * * *" \
  prompt="Generate the NovaMaster nightly infrastructure digest. Collect 24h metrics from Prometheus and Loki, summarize Docker container events, check Uptime Kuma status. Compile into compact Dutch digest. Highlight anomalies." \
  skills=["infra-nightly-digest"] \
  deliver="telegram"
```

## Digest Format

```
🔱 NovaMaster Infra Digest — [Datum] 22:00

📊 SYSTEM
  CPU piek: [%] om [tijd] — avg: [%]
  RAM: [gebruikt]/[totaal] — piek: [%]
  Disk groei: +[MB] in 24u — [%] vrij

🐳 DOCKER
  [X] containers actief — [Y] restarts
  Top CPU: [container] — [%]
  Top RAM: [container] — [MB]

⚠️ FOUTEN (24u)
  [X] ERRORs — [Y] CRITICALs
  Top patroon: [meest voorkomende error]

🌐 UPTIME
  [aantal endpoints] — [X] UP / [Y] DOWN
  SSL: [alle OK / waarschuwing voor X]

🔮 TREND
  [korte trendanalyse — "stabiel", "geheugen lekt langzaam", "disk groeit sneller dan normaal"]
```

## Anomaly Detection

Flag when:
- CPU > 80% for > 30 minutes (unusual load)
- Memory growth > 500MB/day (possible leak)
- Error rate > 2x the weekly average
- Container restarts > 5 in 24h (crash loop)
- Disk growth > 1GB/day (log explosion or runaway process)
- Any P0 service was down for > 5 minutes

## Pitfalls

- Prometheus may not have GPU metrics unless DCGM exporter is running
- Loki log volume can be massive — query with specific filters, not broad scans
- Docker stats reset on daemon restart — cross-check with system uptime
- Uptime Kuma monitoring may be down itself during outages (blind spot)
- If Prometheus or Loki are down, the digest degrades gracefully with partial data
- Timezone: all timestamps in CET (Europe/Amsterdam)
