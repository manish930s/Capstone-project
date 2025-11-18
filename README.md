# Study & Career Co-Pilot – Calendar Bridge

This project exposes a local **Flask** server that talks to **Google Calendar**.
Your Kaggle ADK agent calls this bridge (via Cloudflare Tunnel) to create real
events in your Google Calendar.

---

## 1. Prerequisites

1. **Python 3.10+** installed
2. **pip** installed
3. **VS Code** (for editing)
4. **Cloudflare Tunnel** (`cloudflared`) installed  
   - Download from Cloudflare website and make sure `cloudflared` runs in PowerShell / CMD.
5. A **Google account** with Calendar enabled
6. A **Google Cloud project** with:
   - “Google Calendar API” enabled
   - an **OAuth 2.0 Client ID (Desktop app)** created
   - the **client secret JSON** downloaded

Rename that client file if needed and update `CLIENT_SECRET_FILE` in `calendar_bridge.py`.

---

## 2. Setup this project in VS Code

1. Create a folder on your machine, e.g.:

   ```bash
   mkdir study-career-copilot
   cd study-career-copilot
