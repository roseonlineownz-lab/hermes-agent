#!/usr/bin/env python3
import subprocess
import time
import urllib.request
import urllib.error

def health_check():
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5)
        return req.getcode() == 200
    except Exception:
        return False

def process_exists():
    try:
        result = subprocess.run(["pgrep", "-f", "python3 -m uvicorn"], capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip().split()[0]
            try:
                with open(f"/proc/{pid}/cmdline", "r", encoding="utf-8") as f:
                    cmdline = f.read()
                    if "8000" in cmdline:
                        return True
            except Exception:
                pass
        return False
    except Exception:
        return False

def cleanup_and_restart():
    subprocess.run(["fuser", "-k", "8000/tcp"], capture_output=True)
    time.sleep(1)
    subprocess.Popen(
        ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
        cwd="/home/faramix/NovaMaster/nova-router",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

if not health_check():
    if not process_exists():
        cleanup_and_restart()
        print("NovaRouter restarted on port 8000")
