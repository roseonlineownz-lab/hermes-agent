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

TARGET_DIR="${1:-/tmp/restic-restore-test}"

rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"

restic snapshots --password-file "$RESTIC_PASSWORD_FILE"
echo "Run a manual restore into: $TARGET_DIR"
echo "Example:"
echo "  restic restore latest --target '$TARGET_DIR' --password-file '$RESTIC_PASSWORD_FILE'"
