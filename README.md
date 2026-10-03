# Cloudless Tapo Camera Setup

Set up and run a TP-Link Tapo camera **without the Tapo app, without a TP-Link
cloud account, and without ever giving the camera internet access on your real
network.** Onboard it, create local accounts, configure it, and then move it to
an isolated / air-gapped VLAN where you control it entirely over the LAN
(RTSP, ONVIF, and the local HTTPS API).

Verified on a **TP-Link Tapo C217** (2-pack, 2026-era firmware). The same
approach is known to work on other v3-login Tapo cameras (C2xx family); exact
method schemas vary by model and firmware.

> **Why bother?** Consumer IoT cameras typically require the vendor app and a
> cloud account just to activate, and they phone home continuously afterward.
> There is also growing evidence that smart devices fingerprint the Wi-Fi
> network they are joined to and upload details of it (this was popularized by
> reporting on LG TVs). If you would rather your cameras never see the internet
> and never learn anything about your real network, this is how.

## Scope / ethics

This documents interoperability and local control of **cameras you own**. It
uses a factory-default password that is already public (see Credits) and the
device's own documented provisioning flow. Nothing here defeats encryption you
are not entitled to or targets devices you do not control. Use it on your own
hardware.

## Attribution

This method was worked out through hands-on testing with substantial help from
**GLM 5.3** (the AI model) doing the protocol legwork and scripting, building on
prior public reverse-engineering work (see [CREDITS.md](CREDITS.md)). I am
crediting that openly — I did not do all of this unaided.

## TL;DR

The Tapo app is never needed. A factory-fresh camera exposes a local
provisioning API with a **known default password**, the Wi-Fi join can be
scripted, and once configured the camera can be moved to any network —
including one with no internet — and driven entirely from the LAN.

## Key facts (all verified on hardware)

1. **Default admin password**: `TPL075526460603`. Every Tapo camera with the
   "encrypt v3" login accepts this while factory-fresh. The username is always
   `admin`. (This value is already public — see Credits.)
2. **Setup AP**: a factory-fresh (or reset) camera broadcasts an open Wi-Fi
   network named `Tapo_Cam_<last-4-of-MAC>` and serves its provisioning API at
   `https://192.168.191.1/` (self-signed TLS on port 443). Your machine gets a
   `192.168.191.x/24` lease; the camera is always `192.168.191.1`.
3. **Two API surfaces on that interface**:
   - *Legacy plain path*: `POST /` with raw JSON. Works in AP mode for
     `scanApList`, `connectAp`, `getConnectStatus`.
   - *Encrypted path* (v3 login + `securePassthrough`): two-phase login
     (cnonce -> nonce/device_confirm -> digest_passwd -> stok + AES keys),
     then `POST /stok=<stok>/ds`. Used for account management
     (`setAccountEnabled`, `changeThirdAccount`, `changeAdminPassword`).
   - In AP mode many *other* methods return `-40210` (METHOD_DO_NOT_EXIST).
     That is expected — the full method set unlocks once the camera is
     associated to Wi-Fi.
4. **Wi-Fi password encryption**: the `connectAp` password must be RSA-encrypted
   (PKCS#1 v1.5) with the camera's public key. The AP-mode scan response does
   not carry a per-device key, so the static `pubkey_third_account.pem` from the
   upstream onboarding project is used.
5. **The "internet gate"**: a factory-fresh camera refuses to *complete* the
   first Wi-Fi join unless the target network has working internet
   (`getConnectStatus` returns `-2`). **This gate only applies to first-time
   onboarding.** Once the camera is fully configured it can be moved to an
   isolated network freely.
6. **What the app does during onboarding** (from an MITM capture of the real
   flow): `scanApList` -> `bindToCloud` (skippable!) -> `setLanguage` ->
   `setDeviceLocation` -> `setTimezone` -> `setRecordPlan` -> `connectAp` ->
   `setAccountEnabled` -> `changeThirdAccount` -> `changeAdminPassword`.
   We skip everything except `connectAp`, account setup, password change, and
   timezone — and we never call `bindToCloud`.

## The method, step by step

### Step 0 — Preconditions
- A Linux box with `bash`, `curl`, `jq`, `openssl`, `nmap`, `nmcli`
  (`fzf` optional, for interactive AP selection).
- The two upstream projects (see Credits): the bash onboarding scripts and
  **PyTapo** (correct method schemas for current firmware).
- A Python venv with `pytapo`, `pycryptodome`, `requests`.
- **A throwaway internet source for the one-time activation only** — a phone
  hotspot is ideal. This satisfies the "internet gate" without ever exposing
  your real network to the camera (see the box at the top for why that matters).

> **iOS hotspot caveat:** the hotspot MAC randomizes on every toggle. Use it
> *only* to get through activation. Do **not** leave the camera depending on the
> hotspot — when the MAC changes it orphans itself (solid red LED) and you have
> to re-onboard.

### Step 1 — Connect to the camera's setup AP
Power on a factory-fresh camera, wait for the blinking LED, and join the open
`Tapo_Cam_XXXX` network. You will land on `192.168.191.x`; the camera is
`192.168.191.1`.

### Step 2 — Join the camera to a throwaway internet network
Use the onboarding script (login + scan + AP select + connect over the legacy
path) pointed at your hotspot SSID. The camera gives itself ~60 seconds to
associate. Poll status:

```bash
curl -sk https://192.168.191.1/ -X POST -H 'Content-Type: application/json' \
  -d '{"method":"getConnectStatus","params":{"onboarding":{"get_connect_status":{}}}}'
# status 0 = idle/success, -2 = failed (no internet / wrong password)
```

### Step 3 — Find the camera on that network
```bash
nmap -Pn -p 443,554 --open <SUBNET>/24     # Tapo signature = 443 + 554 open
# verify identity with the default password:
./tapo-onboarding/tCurl.sh <CAMERA_IP> 'TPL075526460603' \
  '[{"method":"getTimezone","params":{"system":{"name":["basic"]}}}]'
```

### Step 4 — Set the accounts (over the encrypted channel)
Three calls in one session (each password hashed per-method):
1. `setAccountEnabled` — enables the "third account" (RTSP/ONVIF).
2. `changeThirdAccount` — creates your streaming user (name is your choice;
    password is MD5-hashed then RSA-encrypted with `pubkey_third_account.pem`).
3. `changeAdminPassword` — your new admin password (SHA256-hashed twice, then
    RSA-encrypted).

Result: `admin` now uses your strong password for the local settings API, and a
separate account of your choosing exists for RTSP/ONVIF.

> **Credential note:** pick a strong password, and keep it out of source
> control. The companion `tapoctl.py` reads it from the `TAPOLIB_PW`
> environment variable — never hardcode it.

### Step 5 — Configure via PyTapo (the real settings API)
```python
from pytapo import Tapo
cam = Tapo("<CAMERA_IP>", "admin", "<your-password>")
cam.setTimezone("UTC-06:00", "America/Chicago")   # example
cam.setOsd("Cam", dateEnabled=True, logoEnabled=False)   # kill the watermark
cam.setPrivacyMode(False)
```
PyTapo carries the correct request schemas for current-generation Tapo firmware
(the classic method names mostly return `-40210`; PyTapo's `setX` wrappers emit
the right wire format).

### Step 6 — Move to the final (isolated) network
The camera remembers its settings. Two routes:
- **Preferred:** if the camera fell back to AP mode (e.g. the hotspot MAC
  changed), reconnect to its setup AP and run the connect script targeting your
  final SSID. The legacy path works, config is preserved, and **no internet is
  needed** because the camera is already activated.
- After the move: `nmap -Pn -p 443,554 --open <FINAL_SUBNET>/24` to find it,
  verify with `tCurl.sh` / PyTapo, and pin its address with a DHCP reservation
  on your router. (Tapo cameras have no static-IP setter; `network.wan` is
  read-only.)
- Reboot to apply: PyTapo `cam.reboot()`, wait ~45 s.

## Ports (station mode)
| Port | Service |
|---|---|
| 443 | Tapo local API (v3 login / securePassthrough / PyTapo) |
| 554 | RTSP — `rtsp://user:pass@<ip>/stream1` (main), `/stream2` (sub) |
| 2020 | ONVIF (device + PTZ service; auth = the streaming account) |
| 8800 | media port (SD clip download, snapshots) |

## Error code cheat sheet
| code | meaning |
|---|---|
| `-40209` | params wrong for this method |
| `-40210` | method doesn't exist (wrong schema, or AP-mode gating) |
| `-40101` | method exists, params invalid |
| `-40401` | session invalid (re-login) |
| `-40413` | rejected login path (e.g. a V4 probe against a v3 camera) |
| `-2` (connect status) | Wi-Fi join failed (bad password / no internet during first onboarding) |

## What's in this repo
- [`README.md`](README.md) — this method writeup.
- [`API.md`](API.md) — local API reference: the CLI, PyTapo, and raw JSON-RPC.
- [`tapoctl.py`](tapoctl.py) — a small CLI over PyTapo
  (`status`/`privacy`/`led`/`daynight`/`image`/`alarm`/`siren`/`reboot`/`raw`).
  Reads host(s) from `TAPOLIB_HOST` and password from `TAPOLIB_PW`.
- [`probe.sh`](probe.sh) — try KLAP + v3 auth against candidate hosts and report
  which transport/account works.
- [`CREDITS.md`](CREDITS.md) — the prior work this stands on, and the AI help.

## See also / credits
Built on [kennedn/tapo-onboarding](https://github.com/kennedn/tapo-onboarding),
[JurajNyiri/PyTapo](https://github.com/JurajNyiri/pytapo), and others —
full list in [CREDITS.md](CREDITS.md). Worked out with help from **GLM 5.3**.
