# Reverse Proxy Hardening

Use this when you expose public services through Caddy or Nginx.

## Baseline rules

- Expose only `80` and `443` on the public interface.
- Bind admin UIs to `127.0.0.1` unless they have auth in front of them.
- Keep internal services on a private Docker network or localhost.
- Redirect HTTP to HTTPS.
- Use modern TLS defaults and keep automatic certificate renewal enabled.
- Add security headers where the app does not already set them.

## Caddy

Recommended focus:

- automatic HTTPS
- `reverse_proxy` only to local backends
- basic auth on admin paths if you must expose them
- access logging for audit trails

## Nginx

Recommended focus:

- TLS 1.2+ / 1.3
- HSTS when the site is stable on HTTPS
- rate limiting on login and admin paths
- `proxy_set_header` correctness for upstream apps

## What not to do

- do not expose multiple admin dashboards directly to the public internet
- do not leave docker-published app ports open if the proxy is already public
- do not rely on TLS as a replacement for firewall rules
