# VPS Ops Bundle

This directory contains the concrete rollout bundle for the VPS upgrades we
selected:

1. Firewall hardening
2. Uptime Kuma monitoring
3. Offsite backups

## Files

- `vps-hardening-plan.md` - rollout order and host firewall guidance
- `docker-compose.uptime-kuma.yml` - local-only monitoring service example
- `restic-backup.sh` - backup job template for offsite object storage

The files are intentionally conservative. They are safe to adapt for a VPS
without exposing new public ports by default.
