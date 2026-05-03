#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  echo "RESTIC_REPOSITORY is required" >&2
  exit 1
fi

if [[ -z "${RESTIC_PASSWORD_FILE:-}" ]]; then
  echo "RESTIC_PASSWORD_FILE is required" >&2
  exit 1
fi

BACKUP_PATHS=(
  "${BACKUP_PATHS_0:-/etc}"
  "${BACKUP_PATHS_1:-/opt}"
  "${BACKUP_PATHS_2:-/home}"
)

EXCLUDES=(
  "--exclude=/var/lib/docker/overlay2"
  "--exclude=/var/lib/docker/containers/*/*.log"
)

restic backup \
  --password-file "$RESTIC_PASSWORD_FILE" \
  "${EXCLUDES[@]}" \
  "${BACKUP_PATHS[@]}"

restic forget \
  --password-file "$RESTIC_PASSWORD_FILE" \
  --keep-daily "${RESTIC_KEEP_DAILY:-7}" \
  --keep-weekly "${RESTIC_KEEP_WEEKLY:-4}" \
  --keep-monthly "${RESTIC_KEEP_MONTHLY:-6}" \
  --prune
