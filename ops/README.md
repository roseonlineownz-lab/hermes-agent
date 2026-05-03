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
- `ufw-hardening.sh` - host firewall baseline
- `crowdsec-setup.sh` - CrowdSec bootstrap helper
- `deploy-uptime-kuma.sh` - start Uptime Kuma from the ops bundle
- `install-restic-service.sh` - install the backup timer and unit files
- `proxy-hardening.md` - reverse proxy hardening notes
- `restore-test.sh` - restore-test helper and manual recovery prompt
- `restic-backup.service` / `restic-backup.timer` - daily backup scheduling
- `restic-backup.env.example` - example environment file for restic

The files are intentionally conservative. They are safe to adapt for a VPS
without exposing new public ports by default.
