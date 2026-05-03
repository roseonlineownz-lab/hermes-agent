#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This setup script currently targets Debian/Ubuntu hosts." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y curl gnupg

if ! command -v crowdsec >/dev/null 2>&1; then
  echo "CrowdSec is not installed yet."
  echo "Follow the official package instructions for your distro, then run:"
  echo "  sudo cscli hub update"
  echo "  sudo cscli collections install crowdsecurity/sshd"
  echo "  sudo cscli collections install crowdsecurity/base-http-scenarios"
  echo "  sudo systemctl enable --now crowdsec"
else
  sudo cscli hub update
  sudo cscli collections install -y crowdsecurity/sshd
  sudo cscli collections install -y crowdsecurity/base-http-scenarios
fi

echo "If you expose nginx or caddy, install the matching bouncer separately."
