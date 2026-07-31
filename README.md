# dash

Personal dashboard stack. One repo, one `docker-compose.yml`, four app services
behind `caddy-docker-proxy`:

| Service | What | URL |
|---|---|---|
| `homeassistant` | Home Assistant (home control + dashboards) | home.namanvashistha.com |
| `glance` | [Glance](https://github.com/glanceapp/glance) personal/info dashboard | dash.namanvashistha.com |
| `docmost` | [Docmost](https://github.com/docmost/docmost) collaborative wiki / docs | docs.namanvashistha.com |
| `beszel` | [Beszel](https://github.com/henrygd/beszel) server + container monitoring | status.namanvashistha.com |

`docmost` is backed by internal-only `docmost-db` (Postgres) and `docmost-redis`
containers — not reverse-proxied, isolated on the internal `docmost` network.
`beszel` is paired with `beszel-agent`, which runs on host networking (so it
measures the host, not a container) and is likewise not reverse-proxied.

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
beszel/                          # created on the server, gitignored
  data/ agent-data/ socket/      #   hub DB, agent keys, hub<->agent socket
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
- **Beszel** is two containers. The hub boots with no config — open
  `status.namanvashistha.com` to create the owner account. The agent needs
  `BESZEL_TOKEN` + `BESZEL_KEY` in `.env` (see `.env.example`), which only exist
  *after* the hub's first boot; until then it restart-loops harmlessly. Once set,
  `docker compose up -d beszel-agent` and add the system in the UI with
  **Host/IP = `/beszel_socket/beszel.sock`** (the port field is ignored — hub and
  agent talk over that shared unix socket, not TCP). The hub also publishes
  `127.0.0.1:8090` so the host-networked agent can reach `HUB_URL`; public
  traffic still goes through Caddy.
- **Networking**: HA uses bridge (to join the `caddy` network), trading away
  mDNS/DHCP auto-discovery. Add integrations by IP/cloud. A Zigbee/Z-Wave USB
  dongle would need `devices:` passthrough (usually host networking) — adjust then.

## Security

`home.namanvashistha.com` is internet-facing and controls the home. Use a strong
owner password + MFA. Consider Cloudflare Access or a VPN in front.

## Tablet

Open `dash.` (info) or `home.` (control) → "Add to Home Screen" for a fullscreen
PWA. For a wall panel use Fully Kiosk Browser (Android).
