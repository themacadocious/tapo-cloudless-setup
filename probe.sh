#!/usr/bin/env bash
# Probe Tapo devices with camera-account credentials (user 'frigate').
# Tries KLAP + v3 on both candidate hosts, reports which auth path works.
# Usage: ./probe_frigate.sh '<password>'
set -euo pipefail
cd "$(dirname "$0")"
PW=$1
[[ -n "$PW" ]] || { echo "usage: $0 '<password>'"; exit 1; }
.venv/bin/python - "$PW" <<'EOF'
import sys, warnings, json; warnings.filterwarnings("ignore")
from pytapo import Tapo
pw = sys.argv[1]
for host in ["192.168.1.50", "192.168.1.51"]:
    for user in ["frigate", "admin"]:
        try:
            cam = Tapo(host, user, pw, printDebugInformation=False)
            tz = cam.getTimezone()
            print(f"SUCCESS host={host} user={user} transport={cam.transport_method} tz={json.dumps(tz)[:80]}")
        except Exception as e:
            print(f"no: host={host} user={user}: {str(e)[:90]}")
EOF
