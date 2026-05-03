#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo install -Dm0644 "${ROOT_DIR}/restic-backup.service" /etc/systemd/system/restic-backup.service
sudo install -Dm0644 "${ROOT_DIR}/restic-backup.timer" /etc/systemd/system/restic-backup.timer
sudo install -Dm0644 "${ROOT_DIR}/restic-backup.env.example" /etc/restic/restic-backup.env
sudo install -Dm0755 "${ROOT_DIR}/restic-backup.sh" /usr/local/bin/restic-backup.sh
sudo systemctl daemon-reload
sudo systemctl enable --now restic-backup.timer
