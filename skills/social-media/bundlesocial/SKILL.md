---
name: bundlesocial
description: "Bundle.social: schedule posts across Twitter/X, LinkedIn, Instagram, TikTok, Facebook, YouTube via one REST endpoint."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [BUNDLESOCIAL_API_KEY]
  commands: [curl]
metadata:
  hermes:
    tags: [Bundlesocial, Social Media, Scheduling, X, LinkedIn, Instagram, TikTok]
    homepage: https://bundle.social
---

# Bundle.social — Cross-platform Post Scheduling

Bundle.social wraps a dozen social platforms behind a single REST API so an agent can post once and fan-out to every channel the user has connected.

## Prerequisites

1. Sign up at https://bundle.social and connect at least one social account (Twitter/X, LinkedIn, Instagram, TikTok, Facebook page, YouTube).
2. Go to **Settings → API** and create an API key.
3. Set the env var:
   ```bash
   export BUNDLESOCIAL_API_KEY=bs_xxxxxxxxxxxxxxxxxxxxxxxxx
   ```

## API basics

- **Base:** `https://api.bundle.social/api/v1`
- **Auth header:** `Authorization: Bearer $BUNDLESOCIAL_API_KEY`
- All payloads are JSON; the `channels` field is a list of provider names like `["twitter", "linkedin"]`.

## Common tasks

### List your connected social accounts
```bash
curl -s "https://api.bundle.social/api/v1/social-accounts" \
  -H "Authorization: Bearer $BUNDLESOCIAL_API_KEY" | python3 -m json.tool
```

### Schedule an immediate text post (cross-channel)
```bash
curl -s -X POST "https://api.bundle.social/api/v1/posts" \
  -H "Authorization: Bearer $BUNDLESOCIAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": ["twitter", "linkedin"],
    "content": "Just shipped a new build of the Nova stack — full notes in the GH release.",
    "publish_at": null
  }'
```

`publish_at: null` posts immediately. Pass an ISO-8601 datetime (e.g. `"2026-05-12T18:30:00Z"`) to schedule.

### Schedule a post with media

Upload first to get a media id:

```bash
curl -s -X POST "https://api.bundle.social/api/v1/media" \
  -H "Authorization: Bearer $BUNDLESOCIAL_API_KEY" \
  -F "file=@./poster.png"
```

Then reference it in the post:

```bash
curl -s -X POST "https://api.bundle.social/api/v1/posts" \
  -H "Authorization: Bearer $BUNDLESOCIAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": ["instagram","linkedin"],
    "content": "Behind-the-scenes shot from todays build.",
    "media_ids": ["med_xxxxxxxxxxxx"],
    "publish_at": "2026-05-12T18:30:00Z"
  }'
```

### List scheduled posts
```bash
curl -s "https://api.bundle.social/api/v1/posts?status=scheduled" \
  -H "Authorization: Bearer $BUNDLESOCIAL_API_KEY"
```

### Cancel a scheduled post
```bash
POST_ID=post_xxxxxxxxxxxx
curl -s -X DELETE "https://api.bundle.social/api/v1/posts/$POST_ID" \
  -H "Authorization: Bearer $BUNDLESOCIAL_API_KEY"
```

## Workflow patterns

- **Daily content drop:** generate text + image with a creative skill (`skills/creative/songwriting-and-ai-music`, `skills/creative/manim-video`), upload the asset, schedule one post to span multiple platforms.
- **Engagement digest:** call `GET /posts?status=published&since=...` once a day to collect engagement counts and feed them back into a memory store.
- **Hand-off to humans:** when the agent isn't sure about tone, POST as a `draft` and link the user to `https://app.bundle.social/posts/<id>` for review.

## Gotchas

- The API enforces per-platform character limits server-side — a single payload that's 380 chars passes for LinkedIn but rejects for Twitter. Split or shorten per-channel if you fan out to short-form platforms.
- Instagram requires media on every post; text-only posts to IG will 400.
- Tokens revoke when the user disconnects an account in the UI. The API returns `account_unavailable` rather than 401 in that case — check the per-channel `status` field in the response, don't rely on top-level HTTP status alone.

## See also

- Mark-XXX integration: `core/integrations/bundlesocial.py` (schedule_post helper)
- `skills/creative/songwriting-and-ai-music/SKILL.md` (generate audio to post)
