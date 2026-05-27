"""Linux/WSL computer-use backend using xdotool + scrot.

Works on any Linux with an X11 display (including WSLg).
Requires: xdotool, scrot (both typically available via apt).
Optional: xclip (clipboard), imagemagick (convert).
"""

from __future__ import annotations

import base64
import logging
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from tools.computer_use.backend import (
    ActionResult,
    CaptureResult,
    ComputerUseBackend,
    UIElement,
)

logger = logging.getLogger(__name__)

_KEY_MAP = {
    "cmd": "super",
    "command": "super",
    "option": "alt",
    "ctrl": "ctrl",
    "shift": "shift",
    "return": "Return",
    "enter": "Return",
    "tab": "Tab",
    "escape": "Escape",
    "esc": "Escape",
    "space": "space",
    "backspace": "BackSpace",
    "delete": "Delete",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "home": "Home",
    "end": "End",
    "pageup": "Prior",
    "pagedown": "Next",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
}


def _run(cmd: List[str], timeout: float = 10.0) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


def _xdotool(*args: str) -> str:
    r = _run(["xdotool", *args])
    if r.returncode != 0:
        raise RuntimeError(f"xdotool {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def linux_computer_use_available() -> bool:
    """True if xdotool + scrot are on PATH and DISPLAY is set."""
    if not shutil.which("xdotool"):
        return False
    if not shutil.which("scrot"):
        return False
    display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    return bool(display)


class LinuxBackend(ComputerUseBackend):
    """Linux/WSL computer-use backend via xdotool + scrot."""

    def __init__(self) -> None:
        self._started = False

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False

    def is_available(self) -> bool:
        return linux_computer_use_available()

    def capture(self, mode: str = "som", app: Optional[str] = None) -> CaptureResult:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            if app:
                wid = self._find_window(app)
                if wid:
                    _run(["scrot", "-o", tmp, "--focused", "-w", str(wid)], timeout=10)
                else:
                    _run(["scrot", "-o", tmp], timeout=10)
            else:
                _run(["scrot", "-o", tmp], timeout=10)

            if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
                return CaptureResult(mode=mode, width=0, height=0, png_b64=None,
                                     elements=[], app=app or "", window_title="")

            with open(tmp, "rb") as fh:
                png_data = fh.read()

            size = self._image_size(tmp)
            w, h = size if size else (0, 0)

            png_b64 = base64.b64encode(png_data).decode("ascii")
            return CaptureResult(
                mode=mode, width=w, height=h, png_b64=png_b64,
                elements=[], app=app or "", window_title="",
                png_bytes_len=len(png_data),
            )
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def click(
        self,
        *,
        element: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        click_count: int = 1,
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        btn_map = {"left": "1", "middle": "2", "right": "3"}
        btn = btn_map.get(button, "1")

        if x is not None and y is not None:
            _xdotool("mousemove", "--sync", str(x), str(y))

        for _ in range(max(1, click_count)):
            _xdotool("click", btn)

        return ActionResult(ok=True, action="click",
                            message=f"clicked {button} at ({x},{y}) x{click_count}")

    def drag(
        self,
        *,
        from_element: Optional[int] = None,
        to_element: Optional[int] = None,
        from_xy: Optional[Tuple[int, int]] = None,
        to_xy: Optional[Tuple[int, int]] = None,
        button: str = "left",
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        if from_xy and to_xy:
            _xdotool("mousemove", "--sync", str(from_xy[0]), str(from_xy[1]))
            _xdotool("mousedown", "1")
            _xdotool("mousemove", "--sync", str(to_xy[0]), str(to_xy[1]))
            _xdotool("mouseup", "1")
            return ActionResult(ok=True, action="drag",
                                message=f"dragged from {from_xy} to {to_xy}")
        return ActionResult(ok=False, action="drag", message="coordinates required")

    def scroll(
        self,
        *,
        direction: str,
        amount: int = 3,
        element: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        if x is not None and y is not None:
            _xdotool("mousemove", "--sync", str(x), str(y))

        scroll_map = {"up": "4", "down": "5", "left": "6", "right": "7"}
        btn = scroll_map.get(direction, "5")

        for _ in range(max(1, amount)):
            _xdotool("click", btn)

        return ActionResult(ok=True, action="scroll",
                            message=f"scrolled {direction} x{amount}")

    def type_text(self, text: str) -> ActionResult:
        _xdotool("type", "--clearmodifiers", "--delay", "12", text)
        return ActionResult(ok=True, action="type", message=f"typed {len(text)} chars")

    def key(self, keys: str) -> ActionResult:
        parts = [k.strip() for k in re.split(r'[+\s]+', keys)]
        translated = []
        for p in parts:
            translated.append(_KEY_MAP.get(p.lower(), p))
        combo = "+".join(translated)
        _xdotool("key", "--clearmodifiers", combo)
        return ActionResult(ok=True, action="key", message=f"pressed {combo}")

    def list_apps(self) -> List[Dict[str, Any]]:
        out = _xdotool("search", "--onlyvisible", "--name", "")
        wids = [w for w in out.split("\n") if w.strip()]
        apps = []
        seen_pids = set()
        for wid in wids[:50]:
            try:
                pid = _xdotool("getwindowpid", wid)
                name = _xdotool("getwindowname", wid)
                if pid not in seen_pids:
                    seen_pids.add(pid)
                    apps.append({"name": name, "pid": int(pid), "window_id": int(wid)})
            except Exception:
                continue
        return apps

    def focus_app(self, app: str, raise_window: bool = False) -> ActionResult:
        wid = self._find_window(app)
        if not wid:
            return ActionResult(ok=False, action="focus_app",
                                message=f"no window matching {app!r}")
        _xdotool("windowactivate", "--sync", str(wid))
        if raise_window:
            _xdotool("windowraise", str(wid))
        return ActionResult(ok=True, action="focus_app", message=f"focused {app}")

    def set_value(self, value: str, element: Optional[int] = None) -> ActionResult:
        if shutil.which("xclip"):
            p = subprocess.Popen(["xclip", "-selection", "clipboard"],
                                 stdin=subprocess.PIPE, env=dict(os.environ, DISPLAY=":0"))
            p.communicate(value.encode())
            _xdotool("key", "ctrl+a")
            _xdotool("key", "ctrl+v")
            return ActionResult(ok=True, action="set_value",
                                message=f"set value via clipboard ({len(value)} chars)")
        self.key("ctrl+a")
        self.type_text(value)
        return ActionResult(ok=True, action="set_value",
                            message=f"set value via type ({len(value)} chars)")

    def _find_window(self, app: str) -> Optional[int]:
        try:
            out = _xdotool("search", "--onlyvisible", "--name", app)
            wids = [w.strip() for w in out.split("\n") if w.strip()]
            return int(wids[0]) if wids else None
        except Exception:
            return None

    def _image_size(self, path: str) -> Optional[Tuple[int, int]]:
        if shutil.which("identify"):
            try:
                r = _run(["identify", "-format", "%w %h", path])
                parts = r.stdout.strip().split()
                if len(parts) >= 2:
                    return (int(parts[0]), int(parts[1]))
            except Exception:
                pass
        return None
