---
name: livekit
description: "LiveKit: realtime voice + video rooms over WebRTC. Mint JWT access tokens, manage rooms, dispatch agents via the server SDK or REST."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]
  commands: [curl, python3]
metadata:
  hermes:
    tags: [LiveKit, Realtime, Voice, Video, WebRTC, Agents]
    homepage: https://docs.livekit.io
---

# LiveKit — Realtime Rooms & Voice Agents

LiveKit provides hosted (LiveKit Cloud) or self-hosted WebRTC infrastructure for voice/video rooms. Use it to give agents a "phone line": one participant is the human, one is the agent process subscribing to the audio track.

## Prerequisites

1. **Cloud:** create a project at https://cloud.livekit.io — read the URL, API key, and API secret from the project's "Settings → Keys" page.
2. **Self-hosted:** see https://docs.livekit.io/home/self-hosting/local — start `livekit-server` with a config file or docker-compose, then mint API key/secret with `livekit-cli create-token`.
3. Set the env vars:
   ```bash
   export LIVEKIT_URL=wss://your-project.livekit.cloud
   export LIVEKIT_API_KEY=APIxxxxxxxxxxxx
   export LIVEKIT_API_SECRET=secretxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

## Mint an access token (HS256 JWT)

Every participant — including the agent — joins with a short-lived JWT signed with the API secret. The token encodes which room they may join and what they may do.

Minimal Python (no third-party deps):

```python
import base64, hmac, hashlib, json, os, time

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def mint_token(room: str, identity: str, ttl=3600,
               can_publish=True, can_subscribe=True) -> str:
    key, secret = os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"]
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "iss": key, "sub": identity, "name": identity,
        "iat": now, "nbf": now, "exp": now + ttl,
        "video": {"room": room, "roomJoin": True,
                  "canPublish": can_publish, "canSubscribe": can_subscribe},
    }
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"

print(mint_token("test-room", "agent-01"))
```

Hand that token to a browser/SDK to join. Tokens are valid for `ttl` seconds — re-mint for long sessions.

## Server SDK (Python)

```bash
pip install livekit-api livekit
```

```python
from livekit import api
async def create_room():
    lkapi = api.LiveKitAPI()  # reads env vars
    room = await lkapi.room.create_room(api.CreateRoomRequest(name="test-room", empty_timeout=300))
    print(room.sid)
```

## Agents framework

For an agent that speaks back: use `livekit-agents` (https://docs.livekit.io/agents/). It wraps STT → LLM → TTS into a `VoiceAgent` worker that joins any room a token grants. Hand it the same `LIVEKIT_URL/API_KEY/API_SECRET` env vars and it runs as a separate process.

## Common Tasks

| Task | How |
|---|---|
| List rooms | `await lkapi.room.list_rooms(api.ListRoomsRequest())` |
| Kick participant | `await lkapi.room.remove_participant(api.RoomParticipantIdentity(room=..., identity=...))` |
| Send data message | `await lkapi.room.send_data(api.SendDataRequest(room=..., data=b"..."))` |
| Generate ingress (RTMP/WHIP push) | `await lkapi.ingress.create_ingress(...)` |
| Generate egress (record to S3) | `await lkapi.egress.start_room_composite_egress(...)` |

## Gotchas

- Tokens are **not** API keys — they identify a participant. Never log a participant token alongside its room name.
- `LIVEKIT_URL` must use `wss://` (or `ws://` for local dev). Browsers reject mixed-scheme.
- A participant `identity` must be unique per room — colliding identities boot the older participant.
- Self-hosted servers behind NAT need TURN configured, or first-time mobile users will hang on "Connecting…".

## See also

- Mark-XXX integration: `core/integrations/livekit.py` (mint_access_token, list_rooms helpers)
- `skills/social-media/bundlesocial/SKILL.md` (publish recorded room artifacts)
