# Tapo Local API Reference

No app, no cloud. All calls go over your LAN to the camera (HTTPS :443).

Set your password once (never hardcode it):
```bash
export TAPOLIB_PW='<your-admin-password>'
export TAPOLIB_HOST='192.168.1.50'      # or a comma-separated list; first reachable wins
```

## Three ways to call the API

### 1. The CLI (easiest)
```bash
./tapoctl.py <command>
# or: python tapoctl.py <command>   (inside a venv with pytapo installed)
```
Commands: `status`, `privacy on|off`, `led on|off`, `daynight auto|day|night`,
`image`, `image <key> <val>`, `alarm`, `siren on|off`, `reboot`,
`raw '<json-array>'`.

Multi-camera: set `TAPOLIB_HOST=192.168.1.50,192.168.1.51` (comma-separated,
first reachable wins). Password comes from `TAPOLIB_PW`.

### 2. PyTapo (full library, 200+ functions)
```python
from pytapo import Tapo
import os
cam = Tapo("192.168.1.50", "admin", os.environ["TAPOLIB_PW"])
cam.setPrivacyMode(True)       # Python API: True/False
print(cam.getPrivacyMode())    # {'enabled': 'off'}
```
The complete function catalog with exact request schemas is in PyTapo's
`pytapo/__init__.py` — any `def getX/setX` there is callable.

### 3. Raw JSON-RPC (what the library generates)
```bash
# via the CLI:
./tapoctl.py raw '[{"method":"getPrivacyMode","params":{"lens_mask":{"get_lens_mask_config":{}}}}]'

# or standalone bash (v3 login + securePassthrough), from the onboarding scripts:
./tapo-onboarding/tCurl.sh 192.168.1.50 "$TAPOLIB_PW" \
  '[{"method":"getTimezone","params":{"system":{"name":["basic"]}}}]'
```
Wire format: HTTPS POST to `https://<ip>/stok=<session-token>/ds`, body =
`{"method":"multipleRequest","params":{"requests":[{method,params},...]}}`,
AES-encrypted inside a `securePassthrough` envelope (tCurl/PyTapo handle this).

## Method naming convention
- Reads: `{"method":"getX","params":{...}}` — usually `{"domain":{"name":[...]}}`,
  e.g. `getTimezone` -> `{"system":{"name":["basic"]}}`.
- Writes: `{"method":"setX","params":{...}}` — usually `{"domain":{"<key>":<val>}}`.
- Batch: several requests in one array; responses come back per-method with a
  per-method `error_code`.
- Error codes: `-40210` = method doesn't exist (wrong name/schema),
  `-40101` = method exists, params wrong, `-40401` = session invalid (re-login).

## Common calls (schema examples)
| Purpose | Method | Params |
|---|---|---|
| Privacy (lens shutter) | getPrivacyMode / setPrivacyMode | `{"lens_mask":{"get_lens_mask_config":{}}}` |
| Timezone | getTimezone / setTimezone | `{"system":{"name":["basic"]}}` / `{"system":{"basic":{"timezone":"UTC-06:00","zone_id":"America/Chicago","timing_mode":"ntp"}}}` |
| Image tuning | getCommonImage / setCommonImage | keys: `luma contrast saturation sharpness chroma inf_delay smartir_level exp_gain ...` |
| Day/night | getDayNightModeConfig / setDayNightMode | mode: 0=auto 1=day 2=night |
| Motion detection | getMotionDetection / setMotionDetection | sensitivity high/normal/low |
| Presets (PTZ) | getPresets / savePreset / deletePreset / moveMotor | |
| Recordings (SD) | getRecordingsList / getRecordingsUTC | |

## Accounts
A configured camera has two local accounts you control (both set during Step 4
of the setup):
- **admin** — the local settings API (PyTapo / tCurl). Password = whatever you
  set with `changeAdminPassword`.
- **your streaming account** (name is your choice; `tapoadmin` is just an
  example) — RTSP/ONVIF: `rtsp://<user>:<pass>@<ip>/stream1` (main),
  `/stream2` (sub).

Neither is the camera's underlying firmware root account, which is not reachable
over any of these interfaces.

## Useful one-liners
```bash
./tapoctl.py status                 # everything at a glance
./tapoctl.py privacy on             # shutter the lens
python -c 'import os;from pytapo import Tapo;c=Tapo(os.environ["TAPOLIB_HOST"],"admin",os.environ["TAPOLIB_PW"]);print(c.getPresets())'
```
