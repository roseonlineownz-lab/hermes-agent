---
name: browser-use-dispatcher
description: Dispatch browser automation tasks via Telegram. Log into sites, check accounts, fill forms, extract data. Uses browser-use + Space Agent. Results delivered back to Telegram.
category: automation
tags: [browser-use, telegram, automation, web, space-agent]
---

# Browser-Use Task Dispatcher

Triggers: user sends a browser task via Telegram, or needs automated web interaction.

## What It Does

1. Receives browser automation tasks via Telegram or CLI
2. Validates the task (safety: no financial transactions, no credential changes)
3. Dispatches to browser-use or Space Agent (:3003)
4. Monitors execution with screenshot checkpoints
5. Delivers results (screenshots, extracted data) back to Telegram

## Safety Boundaries

ALLOWED:
- Log into sites (credentials from ~/.hermes/.env or password manager)
- Check notifications, messages, dashboards
- Extract visible data (prices, status, lists)
- Fill and submit forms (non-financial)
- Monitor pages for changes
- Take screenshots

BLOCKED:
- Financial transactions (payments, transfers, purchases)
- Changing passwords or security settings
- Deleting accounts or data
- Sending messages/making posts without explicit confirmation per message
- Any action on banking, payment, or government sites

## Usage

### From Telegram
```
/browse login op [site] en check notificaties
/browse check prijs van [product] op [site]
/browse haal alle listings op van [marktplaats url]
/browse monitor [url] elke 2 uur — alert als prijs daalt
```

### From CLI
```
browser task "log into LinkedIn and check messages"
browser monitor --url https://example.com --interval 2h --condition "price < 100"
browser extract --url https://site.com/listings --selector ".product-card"
```

## Task Types

| Type | Description | Timeout |
|------|-------------|---------|
| login-check | Log in, take screenshot of first page | 60s |
| data-extract | Navigate, extract structured data | 120s |
| form-fill | Fill and submit a form | 90s |
| monitor | Periodic page check with condition | recurring |
| screenshot | Navigate to URL, capture full page | 45s |

## Execution Flow

1. Task received → validate against safety rules
2. If credentials needed → fetch from ~/.hermes/.env or prompt user
3. Spawn browser-use session with headless Chrome
4. Execute step-by-step with screenshot at each key action
5. On completion: compile result (screenshot + structured data)
6. Deliver to Telegram with link to full session recording
7. Log task to ~/.hermes/data/browser-tasks/

## Credential Management

Credentials stored in ~/.hermes/.env with prefix BROWSER_:
```
BROWSER_LINKEDIN_EMAIL=...
BROWSER_LINKEDIN_PASS=...
BROWSER_TWITTER_EMAIL=...
```

Never expose credentials in task output or screenshots.

## Monitoring Tasks

For recurring monitoring:
```
cronjob create \
  name="Price Monitor [product]" \
  schedule="every 2h" \
  prompt="Run browser-use to check price of [product] at [url]. If price decreased >10% since last check, alert immediately." \
  skills=["browser-use-dispatcher"]
```

## Pitfalls

- Headless detection: some sites block headless browsers — use stealth mode when available
- CAPTCHAs: cannot solve automatically, will screenshot and alert for manual intervention
- Session expiry: logged-in sessions may expire during long monitor intervals — re-authenticate
- Rate limiting: rapid page checks trigger bot protection — minimum 5min between checks on same domain
- Space Agent (:3003) and browser-use compete for the same browser instance — coordinate via lock
- Screenshots with sensitive data are auto-blurred before Telegram delivery
- Telegram has size limits — full page screenshots may need to be split or compressed
