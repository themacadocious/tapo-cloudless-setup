#!/usr/bin/env python3
"""tapoctl — control Tapo cameras locally via PyTapo. No app, no cloud.

Usage:
  tapoctl <command> [args]

Camera is auto-discovered from TAPOLIB_HOST env or default list below.
Credentials: the admin API password is read from the TAPOLIB_PW
environment variable (no default, nothing hardcoded).

Commands:
  status                 device info, timezone, privacy, LED, day/night
  privacy on|off         enable/disable privacy mode (lens shutter)
  led on|off             status LED
  daynight auto|day|night
  image                  print image tuning block
  image <key> <value>    set one image key (e.g. luma 60)
  alarm                  alarm / motion config
  siren on|off           trigger / stop the siren
  reboot                 reboot camera now
  raw '<json-array>'     send raw multipleRequest methods
"""
import sys, os, json, warnings

warnings.filterwarnings("ignore")

HOSTS = os.environ.get("TAPOLIB_HOST", "192.168.1.50").split(",")
PW = os.environ.get("TAPOLIB_PW")
if not PW:
    sys.exit("set TAPOLIB_PW to the camera admin password (nothing is hardcoded)")

def get_cam():
    from pytapo import Tapo
    last = None
    for h in HOSTS:
        h = h.strip()
        if not h:
            continue
        try:
            cam = Tapo(h, "admin", PW, printDebugInformation=False)
            cam.getTimezone()
            return cam, h
        except Exception as e:
            last = e
    print(f"no reachable camera in {HOSTS}: {last}", file=sys.stderr)
    sys.exit(1)

def on_off(v):
    return "on" if v == "on" else "off"

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    cam, host = get_cam()
    if cmd == "status":
        tz = cam.getTimezone()["system"]["basic"]
        print(f"host:      {host}")
        print(f"privacy:   {cam.getPrivacyMode()['enabled']}")
        try: print(f"day/night: {cam.getDayNightModeConfig()}")
        except Exception: pass
        print(f"timezone:  {tz['zone_id']} ({tz['timezone']})")
    elif cmd == "privacy":
        print(json.dumps(cam.setPrivacyMode(sys.argv[2] == "on")))
    elif cmd == "led":
        print(json.dumps(cam.setLEDEnabled(sys.argv[2] == "on")))
    elif cmd == "daynight":
        print(json.dumps(cam.setDayNightMode({"auto": 0, "day": 1, "night": 2}[sys.argv[2]])))
    elif cmd == "image":
        if len(sys.argv) == 2:
            print(json.dumps(cam.getCommonImage(), indent=2))
        else:
            print(json.dumps(cam.executeFunction("setCommonImage", {"image": {"common": {sys.argv[2]: sys.argv[3]}}}))[:200])
    elif cmd == "alarm":
        print(json.dumps(cam.getAlarmConfig(), indent=2)[:800])
    elif cmd == "siren":
        print(json.dumps(cam.setSirenStatus(sys.argv[2] == "on")))
    elif cmd == "reboot":
        print(json.dumps(cam.setReboot(enabled=True)))
    elif cmd == "raw":
        print(json.dumps(cam.executeFunction("multipleRequest", {"requests": json.loads(sys.argv[2])}), indent=2))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
