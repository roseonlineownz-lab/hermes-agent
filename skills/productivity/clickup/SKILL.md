---
name: clickup
description: "ClickUp REST API via curl. Manage tasks, lists, spaces, comments; pull team activity."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [CLICKUP_API_TOKEN]
  commands: [curl]
metadata:
  hermes:
    tags: [ClickUp, Productivity, Tasks, Project Management, API]
    homepage: https://clickup.com/api
---

# ClickUp — Tasks, Lists & Spaces

Drive ClickUp from the CLI via its REST API. No SDK required — `curl` + a personal API token is enough for 90% of automation work.

## Prerequisites

1. Open **ClickUp → Settings → Apps → API Token** (URL: https://app.clickup.com/settings/apps) and copy the personal token (starts with `pk_`).
2. Set the env var:
   ```bash
   export CLICKUP_API_TOKEN=pk_xxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. The token is **scoped to your user** — actions you can't do in the UI you can't do via the API either.

## API basics

- **Base:** `https://api.clickup.com/api/v2`
- **Auth header:** `Authorization: $CLICKUP_API_TOKEN` (no Bearer prefix)
- **Hierarchy:** workspace (team) → space → folder (optional) → list → task

```bash
curl -s "https://api.clickup.com/api/v2/team" \
  -H "Authorization: $CLICKUP_API_TOKEN" | python3 -m json.tool
```

## Common tasks

### List teams / workspaces
```bash
curl -s "https://api.clickup.com/api/v2/team" \
  -H "Authorization: $CLICKUP_API_TOKEN"
```

### List tasks in a list
```bash
LIST_ID=901234567890
curl -s "https://api.clickup.com/api/v2/list/$LIST_ID/task?archived=false&include_closed=false" \
  -H "Authorization: $CLICKUP_API_TOKEN"
```

### Create a task
```bash
curl -s -X POST "https://api.clickup.com/api/v2/list/$LIST_ID/task" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Buy coffee beans","description":"single origin","priority":3}'
```

`priority`: 1 (urgent), 2 (high), 3 (normal), 4 (low). Omit to leave unset.

### Update task status / move task / assign
```bash
TASK_ID=abc123
# update name + status
curl -s -X PUT "https://api.clickup.com/api/v2/task/$TASK_ID" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"New name","status":"in progress"}'
# add assignees
curl -s -X PUT "https://api.clickup.com/api/v2/task/$TASK_ID" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assignees":{"add":[12345],"rem":[]}}'
```

### Add a comment
```bash
curl -s -X POST "https://api.clickup.com/api/v2/task/$TASK_ID/comment" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment_text":"Started on this","notify_all":false}'
```

### Time-tracked entries (last 30 days)
```bash
TEAM_ID=2345678
NOW=$(date +%s)000
START=$(( ($(date +%s) - 60*60*24*30) * 1000 ))
curl -s "https://api.clickup.com/api/v2/team/$TEAM_ID/time_entries?start_date=$START&end_date=$NOW" \
  -H "Authorization: $CLICKUP_API_TOKEN"
```

## Workflow patterns

| Need | Approach |
|---|---|
| Daily standup digest | Pull every task with `due_date_lt=tomorrow_midnight` and group by assignee |
| Auto-create task from agent decision | POST to a dedicated "Inbox" list, tag with `agent-source` custom field |
| Sync with Hermes kanban | Mirror `status` 1:1 (open ↔ "to do", in_progress ↔ "in progress", done ↔ "complete") |

## Gotchas

- The API is **strictly REST** — there is no GraphQL. Pagination uses `?page=0` (zero-indexed) for list endpoints.
- `team_id` in URLs is what the UI calls a "Workspace ID". Confusing but consistent.
- Webhooks (`POST /team/$TEAM_ID/webhook`) require an HTTPS endpoint — they retry with exponential backoff on 5xx but drop on 4xx.
- Custom fields use ID-based access (`custom_fields[i].id` UUID), not name — look up the field once and cache the UUID.

## See also

- Mark-XXX integration: `core/integrations/clickup.py` (list_teams, list_tasks helpers)
- `skills/productivity/linear/SKILL.md` (similar shape, different provider)
