#!/bin/sh
# ---------------------------------------------------------------------------
# homepage-autodiscover
# Reads every container's `caddy:` label off the docker socket and writes
# Homepage's services.yaml. New container with a caddy label -> new card,
# automatically. Mirrors AutoKuma's `!caddy` discovery.
#
# Optional curation: if services.header.yaml exists, it is prepended verbatim
# (use it for services that need a widget, e.g. Home Assistant). Any container
# named in a `container:` line there is skipped from auto-discovery so it isn't
# listed twice.
# ---------------------------------------------------------------------------
set -u
OUT=/config/services.yaml
HEADER=/config/services.header.yaml
INTERVAL="${INTERVAL:-30}"

emit() {
  tmp=$(mktemp)
  skip=""
  if [ -f "$HEADER" ]; then
    cat "$HEADER" > "$tmp"
    printf '\n' >> "$tmp"
    skip=$(grep -E '^[[:space:]]*container:' "$HEADER" | sed -E 's/.*container:[[:space:]]*//')
  fi
  printf '# --- auto-discovered from caddy: labels. Managed by homepage-autodiscover; do not edit. ---\n' >> "$tmp"
  printf -- '- Discovered:\n' >> "$tmp"
  any=0
  for name in $(docker ps --format '{{.Names}}' | sort); do
    printf '%s\n' "$skip" | grep -qx "$name" && continue
    label=$(docker inspect -f '{{ index .Config.Labels "caddy" }}' "$name" 2>/dev/null)
    case "$label" in
      http://*|https://*) : ;;
      *) continue ;;
    esac
    # first host only; strip scheme and any path/comma-separated extras
    host=$(printf '%s' "$label" | sed -E 's#^https?://##; s#[/,[:space:]].*$##')
    [ -z "$host" ] && continue
    {
      printf '    - %s:\n' "$name"
      printf '        href: https://%s\n' "$host"
      printf '        icon: %s.png\n' "$name"
      printf '        server: my-docker\n'
      printf '        container: %s\n' "$name"
    } >> "$tmp"
    any=1
  done
  [ "$any" = 0 ] && printf '    - none found:\n        description: no containers carry a caddy label\n' >> "$tmp"

  if ! cmp -s "$tmp" "$OUT" 2>/dev/null; then
    cp "$tmp" "$OUT" && printf '[autodiscover] services.yaml updated\n'
  fi
  rm -f "$tmp"
}

printf '[autodiscover] starting; polling every %ss\n' "$INTERVAL"
while true; do
  emit
  sleep "$INTERVAL"
done
