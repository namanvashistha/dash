"""Reconcile ConOps' registered apps to apps.json.

ConOps has no declarative bootstrap: its only source of truth is the SQLite
database in the conops_data volume, written through the API. So the set of
deployed stacks lives nowhere in git by default, and rebuilding it after losing
that volume is a from-memory exercise. apps.json is the checked-in desired
state; this script applies it.

Idempotent, keyed on app name. Apps already present are skipped, never PATCHed —
an app edited by hand in the UI is a deliberate act, and silently reverting it
would be worse than leaving the drift visible in the summary below.

Runs as the `conops-register` service in docker-compose.yml: a one-shot on the
`caddy` network, gated on ConOps' healthcheck, which exits 0 and stays exited.
That is why ConOps needs no published host port — this reaches it as
`conops:8080` over docker DNS.

Standard library only, so the tool image can stay a stock python:alpine with
nothing installed into it.

Re-run without disturbing the stack:
    docker compose run --rm conops-register
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("CONOPS_URL", "http://conops:8080").rstrip("/")
APPS_FILE = os.environ.get("CONOPS_APPS_FILE", "/conops/apps.json")
TIMEOUT = 30


def request(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read().decode()
    return json.loads(body) if body.strip() else None


class UnknownShape(Exception):
    """The list endpoint returned something we cannot interpret."""


def list_apps():
    """Return the registered apps.

    ConOps wraps responses in {"message": ..., "data": [...]} (internal/api
    /types.go). `data` carries omitempty, so it is absent entirely when no apps
    are registered — an empty list and a missing key mean the same thing here.

    Anything else raises rather than degrading to "nothing is registered".
    ConOps enforces no uniqueness on app names, so a wrong answer here does not
    fail: it silently registers a second copy of every app, and each copy gets
    its own UUID compose project. That is how you end up with three parallel
    stacks per app, all fighting over the same caddy labels.
    """
    body = request("GET", "/api/v1/apps/")
    if body is None:
        return []
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        apps = body.get("data", body.get("apps", []))
        if apps is None:
            return []
        if isinstance(apps, list):
            return apps
    raise UnknownShape(f"unrecognised list response: {str(body)[:200]}")


def main():
    try:
        desired = json.load(open(APPS_FILE))
    except (OSError, ValueError) as exc:
        sys.exit(f"cannot read {APPS_FILE}: {exc}")

    try:
        existing = {a.get("name") for a in list_apps() if isinstance(a, dict)}
    except (urllib.error.URLError, OSError) as exc:
        sys.exit(f"cannot reach ConOps at {BASE}: {exc}")
    except UnknownShape as exc:
        # Refuse to register rather than risk duplicating every app.
        sys.exit(f"cannot determine what is already registered, aborting: {exc}")

    failed = False
    seen = set()
    for app in desired:
        name = app.get("name")
        if not name:
            print("SKIP     (entry with no name)", file=sys.stderr)
            failed = True
            continue
        if name in seen:
            # apps.json itself listing a name twice would otherwise create two
            # projects in one run.
            print(f"SKIP     {name} (duplicate entry in apps.json)", file=sys.stderr)
            failed = True
            continue
        seen.add(name)
        if name in existing:
            print(f"skip     {name} (already registered)")
            continue
        try:
            request("POST", "/api/v1/apps/", app)
            print(f"register {name}")
        except urllib.error.HTTPError as exc:
            print(f"FAILED   {name}: {exc.code} {exc.read().decode()[:200]}", file=sys.stderr)
            failed = True
        except (urllib.error.URLError, OSError) as exc:
            print(f"FAILED   {name}: {exc}", file=sys.stderr)
            failed = True

    final = [a for a in list_apps() if isinstance(a, dict)]
    print("\nRegistered apps:")
    for a in sorted(final, key=lambda x: x.get("name") or ""):
        print(
            f"  {a.get('name', '?'):12s} "
            f"{a.get('status', '?'):10s} "
            f"{a.get('branch', '?')}"
        )

    # Duplicate names mean duplicate compose projects — parallel stacks on the
    # same caddy labels. Surface it loudly; ConOps will not.
    names = [a.get("name") for a in final]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        print(f"\nWARNING: duplicate registrations: {', '.join(dupes)}", file=sys.stderr)
        print("Each duplicate runs its own stack. Delete the extras.", file=sys.stderr)
        failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
