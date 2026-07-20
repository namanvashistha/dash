# homeassistant

Home Assistant deployment for `home.namanvashistha.com`.

Runs the official prebuilt image behind `caddy-docker-proxy` — no source fork, no
build step. Deployed by the central `deploy.sh` (in the `namanvashistha.github.io`
repo) which clones/pulls this repo and runs `docker compose up -d --build`.

## Layout

```
docker-compose.yml          # official HA image + caddy routing labels
config/configuration.yaml   # reverse-proxy trust + default_config
config/automations.yaml     # HA edits these via the UI; versioned here
config/scripts.yaml
config/scenes.yaml
```

Everything else HA writes into `config/` at runtime (database, secrets, `.storage`)
is gitignored.

## Deploy

Add to `deploy.sh` REPOS in the main site repo:

```
"homeassistant|https://github.com/namanvashistha/homeassistant.git"
```

then run `deploy.sh` on the server. First boot takes ~1 min while HA initializes.
Open **https://home.namanvashistha.com** and create the owner account.

## Networking note

Uses **bridge** networking so it can join the `caddy` network for reverse-proxy
routing. This trades away mDNS/DHCP device auto-discovery — add integrations by IP
or cloud instead. If you later add a Zigbee/Z-Wave USB dongle, that needs a
`devices:` passthrough (and usually host networking); adjust the compose then.

## Security

`home.namanvashistha.com` is internet-facing and controls the home. Use a strong
owner password and enable MFA in HA. Consider fronting it with Cloudflare Access or
a VPN for anything beyond a strong password.

## Tablet dashboard

HA's built-in Lovelace dashboard *is* the tablet dashboard. On the tablet: open the
URL → "Add to Home Screen" for a fullscreen PWA. For a wall panel, pair with **Fully
Kiosk Browser** (Android) and the **Kiosk Mode** custom card (via HACS) to hide the
header/sidebar.
