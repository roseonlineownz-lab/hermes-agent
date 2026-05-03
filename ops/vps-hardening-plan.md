# VPS Hardening Plan

This is the concrete order I would apply on a typical VPS with public
services:

1. Firewall hardening
2. Uptime Kuma monitoring
3. Offsite backups

## 1. Firewall hardening

Start with a deny-by-default host firewall. Open only the ports that are
actually needed.

Typical baseline:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

If you use Docker, remember that published container ports can bypass a naive
host firewall setup. Prefer one of these patterns:

- bind internal services to `127.0.0.1`
- expose only the reverse proxy on `80/443`
- keep sensitive admin UIs private and access them through SSH tunnels

Add CrowdSec after the firewall if you want automatic brute-force blocking on
SSH and web traffic. Use Fail2ban only if you want the simplest possible log
based defense.

## 2. Uptime Kuma monitoring

Run Uptime Kuma locally and keep the UI private.

Recommended pattern:

- bind the service to `127.0.0.1`
- store state in a persistent volume
- monitor:
  - HTTP/HTTPS endpoints
  - TCP ports
  - TLS certificate expiry
  - host reachability
- connect one alert channel first and test it immediately

## 3. Offsite backups

Use object storage as the primary offsite backup target.

Recommended default:

- `restic` or `borg`
- `Backblaze B2` or `S3`
- monthly restore test to a clean host

Backup scope:

- compose files
- environment files
- persistent volumes
- database dumps
- reverse proxy config
- SSH/config bootstrap files you would need to rebuild the host

Do not rely on snapshots alone. Snapshots are useful for fast rollback, but
they are not a complete offsite recovery plan.

## Rollout sequence

1. Verify which ports actually need to be public.
2. Apply host firewall rules.
3. Confirm SSH still works from a second session.
4. Add CrowdSec or Fail2ban.
5. Deploy Uptime Kuma locally and add monitors.
6. Configure `restic`/`borg` with offsite storage.
7. Run a test restore and document the result.
