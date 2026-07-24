# dash

Personal dashboard stack. One repo, one `docker-compose.yml`, three app services
behind `caddy-docker-proxy`:

| Service | What | URL |
|---|---|---|
| `homeassistant` | Home Assistant (home control + dashboards) | home.namanvashistha.com |
| `glance` | [Glance](https://github.com/glanceapp/glance) personal/info dashboard | dash.namanvashistha.com |
| `docmost` | [Docmost](https://github.com/docmost/docmost) collaborative wiki / docs | docs.namanvashistha.com |

`docmost` is backed by internal-only `docmost-db` (Postgres) and `docmost-redis`
containers — not reverse-proxied, isolated on the internal `docmost` network.

Deployed by the central `deploy.sh` (in the `namanvashistha.github.io` repo), which
clones/pulls this repo and runs `docker compose up -d --build`. One compose file
brings both containers up together.

## Layout

```
docker-compose.yml               # both services + caddy routing labels
homeassistant/config/            # HA config (rest is runtime, gitignored)
  configuration.yaml             #   reverse-proxy trust + default_config
  automations.yaml scripts.yaml scenes.yaml
glance/glance.yml                # Glance dashboard config
```

## Deploy

Entry in `deploy.sh` REPOS (main site repo):

```
"dash|https://github.com/namanvashistha/dash.git"
```

then run `deploy.sh` on the server. Live at **home.** and **dash.**namanvashistha.com.

## Notes

- **HA pinned to `2026.6`**: `:stable` ships 2026.7 on Python 3.14, which deadlocks
  at boot (`ImportExecutor` hang, 0% CPU, never binds 8123). 2026.6 is the last
  Python-3.13 minor. Revisit `:stable` once HA's 3.14 boot bug is fixed.
- **`http://` scheme on Caddy labels is required** — `deploy.sh` runs Caddy with
  `auto_https=off` behind Cloudflare; a scheme-less site address breaks routing.
- **Glance** reads `glance/glance.yml` and the read-only docker socket (for the
  container-status widget). Edit `glance.yml` → `docker compose restart glance`.
- **Docmost** needs `DOCMOST_APP_SECRET` and `DOCMOST_DB_PASSWORD` set in `.env`
  before first boot (see `.env.example`). Docs live in the Postgres DB; only
  attachments/avatars are on the `docmost-storage` volume. First run auto-creates
  the schema — open `docs.namanvashistha.com` to set up the owner account.
- **Networking**: HA uses bridge (to join the `caddy` network), trading away
  mDNS/DHCP auto-discovery. Add integrations by IP/cloud. A Zigbee/Z-Wave USB
  dongle would need `devices:` passthrough (usually host networking) — adjust then.

## Security

`home.namanvashistha.com` is internet-facing and controls the home. Use a strong
owner password + MFA. Consider Cloudflare Access or a VPN in front.

## Tablet

Open `dash.` (info) or `home.` (control) → "Add to Home Screen" for a fullscreen
PWA. For a wall panel use Fully Kiosk Browser (Android).
