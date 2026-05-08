---
name: firecrawl-lead-intel
description: Firecrawl-powered lead intelligence pipeline — scrape target sites, extract company data, score leads, push to n8n. Core sales automation.
category: automation
tags: [firecrawl, lead-gen, n8n, sales, scraping]
---

# Firecrawl Lead Intelligence Pipeline

Triggers: user mentions "lead gen", "firecrawl leads", "scrape prospects", or asks to find leads in a specific niche.

## What It Does

1. Accepts a target niche, industry, or URL list
2. Uses Firecrawl API to scrape and extract structured data
3. Identifies: company name, industry, size signals, decision-maker hints, tech stack indicators
4. AI-scores each lead (1-10) using DeepSeek V4 Pro (cost-efficient for bulk)
5. Pushes scored leads to n8n webhook for downstream processing (CRM, email sequences, enrichment)
6. Saves raw results to ~/.hermes/data/leads/ for audit trail

## Required APIs / Setup

- Firecrawl API key in ~/.hermes/.env as FIRECRAWL_API_KEY
- n8n webhook URL configured in ~/.hermes/config.yaml under firecrawl_lead_intel.n8n_webhook
- DeepSeek V4 Pro available via LiteLLM (:4000) or direct Ollama

## Usage

### From Telegram
```
/leadgen SaaS bedrijven in Amsterdam
/leadgen cybersecurity startups in London
/leadgen https://example.com/partners —scrape-partners
```

### From Hermes CLI
```
firecrawl lead intel: e-commerce bedrijven met >50 werknemers in Nederland
```

### From n8n Trigger
n8n workflow fires a webhook → Hermes picks up → scrapes → scores → pushes back to n8n.

## Pipeline Steps

1. **Query expansion** — enrich niche keywords for broader coverage
2. **Firecrawl search** — search + scrape target domains
3. **Structured extraction** — pull company name, description, contact hints, tech signals
4. **AI scoring** — rate each lead 1-10 on: relevance, size signal, buying intent signals, tech-stack match
5. **n8n push** — POST scored leads to n8n webhook
6. **Summary** — return top 10 leads with scores to Telegram/CLI

## Scoring Rubric

| Factor | Weight | Indicators |
|--------|--------|------------|
| Relevance | 30% | Matches niche, industry keywords |
| Size Signal | 20% | Employee count hints, office locations, "enterprise" language |
| Buying Intent | 25% | Pricing page, "demo" CTA, case studies, growth language |
| Tech Stack | 15% | Modern stack signals (React, Kubernetes, AI/ML mentions) |
| Contactability | 10% | Public email, contact form, LinkedIn presence |

## Output Format

```
🔱 Lead Intel: [niche] — [aantal] leads gevonden

Top 10:
1. Bedrijf X — Score 9.2 — tech stack: React, AWS — contact@x.com
2. Bedrijf Y — Score 8.7 — 50-200 werknemers — demo CTA actief
...

Gepushed naar n8n. Raw data: ~/.hermes/data/leads/[timestamp].json
```

## Pitfalls

- Firecrawl rate limits: max 10 concurrent scrapes. Batch large lists.
- Some sites block scrapers — Firecrawl handles most, but flag failures
- AI scoring costs: ~10K tokens per 100 leads with DeepSeek V4 Pro (~$0.05)
- Lead data goes stale fast — timestamp everything, re-scrape after 30 days
- n8n webhook must be reachable from WSL (use host.docker.internal or direct localhost)
