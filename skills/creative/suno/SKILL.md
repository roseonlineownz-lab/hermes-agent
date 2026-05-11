---
name: suno
description: "Suno: generate music tracks from a prompt + tags. Works with the official paid API or any OSS suno-api / sunoapi.org proxy."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [SUNO_API_KEY]
  commands: [curl]
metadata:
  hermes:
    tags: [Suno, Music, Audio Generation, Creative]
    homepage: https://suno.com
---

# Suno — Music Generation

Suno generates short songs (~2 min) from a text prompt and a comma-separated `tags` string (style hints: `lofi, jazz, female vocals`). There is no fully-stable public v1 API yet — the de-facto endpoints are either:

1. The OSS proxy at https://github.com/gcui-art/suno-api (self-host, uses your suno.com cookie)
2. Hosted proxies like https://sunoapi.org / https://api.sunoapi.com

Both expose **the same `POST /api/generate` + `GET /api/get?ids=…` shape**, so a single client works for everything.

## Prerequisites

1. Either:
   - Get a session cookie from suno.com (DevTools → Application → Cookies → `__client`) and run the OSS proxy locally
   - Sign up at sunoapi.org and grab an API key
2. Set env vars:
   ```bash
   export SUNO_API_KEY=sk_xxxxxxxxxxxxxxxxxxx
   export SUNO_API_BASE=https://api.sunoapi.org   # or http://localhost:3000 for self-host
   ```

## API basics

- **Auth:** `Authorization: Bearer $SUNO_API_KEY`
- **Generation is async:** `POST /api/generate` returns one or two clip ids; poll `GET /api/get?ids=...` until each clip's `status` is `complete` (then `audio_url` is set).

## Generate a track

```bash
curl -s -X POST "$SUNO_API_BASE/api/generate" \
  -H "Authorization: Bearer $SUNO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A late-night drive through Tokyo with neon reflections, melancholy mood",
    "tags": "synthwave, slow tempo, instrumental",
    "make_instrumental": true,
    "mv": "chirp-v3-5"
  }'
```

Response:
```json
{ "data": [{ "id": "clip-abc", "status": "queued" }, { "id": "clip-def", "status": "queued" }] }
```

## Poll for completion

```bash
curl -s "$SUNO_API_BASE/api/get?ids=clip-abc,clip-def" \
  -H "Authorization: Bearer $SUNO_API_KEY"
```

When `status: "complete"` appears, the response contains `audio_url`, `image_url`, `title`, and `lyrics`. Download with:

```bash
curl -sLO "$AUDIO_URL"
```

## Common task: generate + download in one go

```bash
gen=$(curl -s -X POST "$SUNO_API_BASE/api/generate" \
  -H "Authorization: Bearer $SUNO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"upbeat morning jazz","tags":"jazz, piano, female vocals","make_instrumental":false,"mv":"chirp-v3-5"}')
ids=$(echo "$gen" | python3 -c 'import json,sys; print(",".join(c["id"] for c in json.load(sys.stdin)["data"]))')
echo "queued: $ids"
for i in $(seq 1 60); do
  status=$(curl -s "$SUNO_API_BASE/api/get?ids=$ids" -H "Authorization: Bearer $SUNO_API_KEY")
  ready=$(echo "$status" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(all(c.get("status")=="complete" for c in d["data"]))')
  if [[ "$ready" == "True" ]]; then
    echo "$status" | python3 -c 'import json,sys; [print(c["audio_url"]) for c in json.load(sys.stdin)["data"]]'
    break
  fi
  sleep 5
done
```

## Workflow patterns

- **Soundtrack a video:** generate music → feed the duration to a creative-ideation skill → render with `skills/creative/manim-video`.
- **Daily song:** schedule with `cron` (`skills/devops/...`) and post via `skills/social-media/bundlesocial`.
- **Custom voice cloning** is not exposed via this API. Use ElevenLabs or `skills/creative/songwriting-and-ai-music` for that.

## Gotchas

- The OSS proxy at `gcui-art/suno-api` uses your suno.com **cookie**, not an API key. Cookies expire — refresh weekly or after any password change.
- Generation typically takes 40-90s. Don't poll faster than once every 3-5s or you risk getting rate-limited by the proxy.
- The model identifier (`mv`) accepts `chirp-v3-0`, `chirp-v3-5`, etc. New revisions show up in the suno.com UI before they're documented — try the latest UI version if outputs feel stale.

## See also

- Mark-XXX integration: `core/integrations/suno.py` (generate + fetch helpers, URL-encodes ids correctly)
- `skills/creative/songwriting-and-ai-music/SKILL.md` (broader music-generation guidance)
