"""
GimmeDat v1.0.1 — a free-forever desktop video downloader.
Backend : open-source media tools + bundled ffmpeg (imageio-ffmpeg)
UI      : customtkinter responsive GRID layout, with a tkinter Canvas glitch
          layer behind and a pixel-cat mascot.

GimmeDat — made by Kaiden.
Copyright (C) 2026 Kaiden.
Licensed under the GNU General Public License v3.0 (see the LICENSE file).
This is free software and comes with ABSOLUTELY NO WARRANTY; you may
redistribute it under the terms of the GPL. Don't strip the credit.

Responsive: the window resizes/maximizes and everything reflows via grid weights
(the quality grid re-wraps on width). Honest motion note: tkinter tops out near
~15fps; animations move/recolor items rather than redraw — smooth-enough, not
60fps. For true motion graphics use a web (Tauri/Electron) or Qt/QML stack.

All knobs live in the CONFIG block below.
"""

import os
import re
import sys
import json
import math
import random
import threading
import webbrowser
import urllib.request
from io import BytesIO
from pathlib import Path

import tkinter as tk
import customtkinter as ctk
import yt_dlp
from PIL import Image, ImageTk

try:
    from tkinterdnd2 import TkinterDnD, DND_TEXT, DND_FILES
    _HAS_DND = True
except Exception:
    _HAS_DND = False

# Background music uses Windows MCI (winmm) via ctypes — no extra dependency,
# plays + loops MP3 and bundles into the .exe with nothing to install.
import ctypes
_HAS_MCI = hasattr(ctypes, "windll")

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

VERSION          = "1.0.1"
APP_NAME         = "GimmeDat"

BUYMEACOFFEE_URL = "https://buymeacoffee.com/ridhakaiden"
PAYPAL_URL       = "https://paypal.me/1mkaiden"

DEFAULT_GEO      = "980x760"
MIN_W, MIN_H     = 840, 600

ENABLE_MUSIC     = False                       # looping background music, off by default
BGM_FILE         = "assets/bgm.mp3"            # 8-bit no-copyright soundtrack

# clean cyberpunk palette: near-black + purple/violet + ONE neon accent (cyan)
BG       = "#08070d"
PANEL    = "#0e0c16"
CARD     = "#13101f"
CARD2    = "#181327"
BORDER   = "#271f3e"
GLOW     = "#3b2d63"
PURPLE   = "#7c3aed"
VIOLET   = "#8b5cf6"
PURPLE_L = "#a78bfa"
NEON     = "#22d3ee"
NEON_DIM = "#0e7490"
TEXT     = "#ece9fb"
MUTED    = "#8b85b0"
FAINT    = "#544d77"
OK       = "#34d399"
ERR      = "#fb7185"

F_DISP = "Arial Black"
F_MONO = "Consolas"

# label, regex patterns, accent color, original icon kind (NOT brand logos)
PLATFORMS = {
    "youtube":    {"label": "YouTube",     "color": "#ff4d4d", "icon": "play",
                   "patterns": [r"youtu\.be", r"youtube\.com", r"yt\.be"]},
    "tiktok":     {"label": "TikTok",      "color": "#22e3b2", "icon": "play",
                   "patterns": [r"tiktok\.com", r"vm\.tiktok"]},
    "instagram":  {"label": "Instagram",   "color": "#d96bf0", "icon": "camera",
                   "patterns": [r"instagram\.com", r"instagr\.am"]},
    "pinterest":  {"label": "Pinterest",   "color": "#ff4d6d", "icon": "pin",
                   "patterns": [r"pinterest\.", r"pin\.it"]},
    "twitter":    {"label": "Twitter",     "color": "#3aa0ff", "icon": "play",
                   "patterns": [r"twitter\.com", r"x\.com", r"t\.co"]},
    "facebook":   {"label": "Facebook",    "color": "#3b7bff", "icon": "play",
                   "patterns": [r"facebook\.com", r"fb\.com", r"fb\.watch"]},
    "reddit":     {"label": "Reddit",      "color": "#ff6a3d", "icon": "play",
                   "patterns": [r"reddit\.com", r"redd\.it", r"v\.redd\.it"]},
    "soundcloud": {"label": "SoundCloud",  "color": "#ff7a3d", "icon": "wave",
                   "patterns": [r"soundcloud\.com"]},
    "vimeo":      {"label": "Vimeo",       "color": "#3ac0ff", "icon": "play",
                   "patterns": [r"vimeo\.com"]},
    "twitch":     {"label": "Twitch",      "color": "#9d6bff", "icon": "play",
                   "patterns": [r"twitch\.tv"]},
    "dailymotion":{"label": "Dailymotion", "color": "#3a9bff", "icon": "play",
                   "patterns": [r"dailymotion\.com", r"dai\.ly"]},
    "bilibili":   {"label": "Bilibili",    "color": "#ff8fb3", "icon": "play",
                   "patterns": [r"bilibili\.com", r"b23\.tv"]},
}

QUALITY_TIERS = [("4K", 2160), ("2K", 1440), ("1080p", 1080), ("720p", 720),
                 ("480p", 480), ("360p", 360), ("240p", 240), ("MP3", "audio")]

STATS_FILE = Path.home() / ".gimmedat" / "stats.json"

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / rel


def get_ffmpeg():
    import shutil
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def detect_platform(url: str):
    for key, info in PLATFORMS.items():
        for pat in info["patterns"]:
            if re.search(pat, url, re.IGNORECASE):
                return key
    return None


def find_urls(text: str):
    raw = re.findall(r"https?://[^\s<>{}\"']+", text or "")
    return [u for u in raw if detect_platform(u)]


def default_download_root() -> Path:
    """Default save location — a single flat folder, no per-platform subdirs."""
    root = Path.home() / "Downloads" / "GimmeDat Downloads"
    root.mkdir(parents=True, exist_ok=True)
    return root


def human_size(n):
    if not n:
        return ""
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def fmt_duration(s):
    if not s:
        return ""
    s = int(s)
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def clean_error(msg: str) -> str:
    m = (msg or "").lower()
    if "private" in m:                            return "This video is private 🔒"
    if "sign in" in m or "age" in m:              return "Age-restricted — needs a login 🔞"
    if "geo" in m or "your country" in m or "not available in" in m:
        return "Region-locked in your country 🌍"
    if "removed" in m or "unavailable" in m or "deleted" in m or "does not exist" in m:
        return "Video unavailable or removed ✗"
    if "404" in m or "not found" in m:            return "Not found (404) — check the link"
    if "unsupported url" in m:                    return "That link isn't supported"
    if "timed out" in m or "connection" in m:     return "Network hiccup — try again"
    return "Couldn't grab that — the link may be broken"


# ─────────────────────────────────────────────────────────────────────────────
#  PLATFORM ICONS — simple ORIGINAL glyphs (never trademarked logos). Drawn on a
#  tiny canvas in the platform's accent color; swappable via assets/platform_<k>.png
# ─────────────────────────────────────────────────────────────────────────────

def make_icon(parent, plat_key, size=22, bg=CARD):
    info = PLATFORMS.get(plat_key, {})
    color = info.get("color", NEON)
    kind = info.get("icon", "dot")
    c = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)

    # PNG override?
    png = resource_path("assets") / f"platform_{plat_key}.png"
    if png.exists():
        try:
            img = ImageTk.PhotoImage(Image.open(png).convert("RGBA").resize((size, size)))
            c.image = img
            c.create_image(size // 2, size // 2, image=img)
            return c
        except Exception:
            pass

    p, q = size * 0.2, size * 0.8
    mid = size / 2
    if kind == "play":
        c.create_polygon(p, p, p, q, q, mid, outline=color, fill="", width=2)
    elif kind == "pin":
        c.create_oval(p, p * 0.8, q, q * 0.95, outline=color, fill="", width=2)
        c.create_line(mid, q * 0.9, mid, size - 1, fill=color, width=2)
    elif kind == "camera":
        c.create_rectangle(p, p + 2, q, q, outline=color, fill="", width=2)
        c.create_oval(mid - 3, mid - 2, mid + 3, mid + 4, outline=color, fill="", width=2)
    elif kind == "wave":
        for i, hh in enumerate((0.3, 0.6, 0.45, 0.75)):
            x = p + i * (q - p) / 3
            c.create_line(x, mid + size * hh / 2, x, mid - size * hh / 2,
                          fill=color, width=2)
    else:  # dot
        c.create_oval(mid - 4, mid - 4, mid + 4, mid + 4, outline="", fill=color)
    return c


# ─────────────────────────────────────────────────────────────────────────────
#  STATS  — persisted JSON (files, bytes, last file, window geometry)
# ─────────────────────────────────────────────────────────────────────────────

class Stats:
    def __init__(self):
        self.count = 0
        self.bytes = 0
        self.last = None
        self.geometry = None
        self.download_dir = None       # user's chosen save folder (None = default)
        self._load()

    def _load(self):
        try:
            d = json.loads(STATS_FILE.read_text(encoding="utf-8"))
            self.count = d.get("count", 0)
            self.bytes = d.get("bytes", 0)
            self.last = d.get("last")
            self.geometry = d.get("geometry")
            self.download_dir = d.get("download_dir")
        except Exception:
            pass

    def save(self):
        try:
            STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATS_FILE.write_text(json.dumps(
                {"count": self.count, "bytes": self.bytes,
                 "last": self.last, "geometry": self.geometry,
                 "download_dir": self.download_dir}, indent=2),
                encoding="utf-8")
        except Exception:
            pass

    def add(self, size, last):
        self.count += 1
        self.bytes += int(size or 0)
        self.last = last
        self.save()


# ─────────────────────────────────────────────────────────────────────────────
#  PIXEL MASCOT  — minimal cyber-cat from squares, animated by MOVING the group.
# ─────────────────────────────────────────────────────────────────────────────

CAT = [
    "B.......B..",
    "BB.....BB..",
    "BBBBBBBBBB.",
    "BBBBBBBBBB.",
    "BEBBBBBBEB.",
    "BBBBBBBBBB.",
    "BBBBBBBBBBB",
    "BBBBBBBBB.B",
    "BBBBBBBBB.B",
    ".BB...BB...",
]

class Mascot:
    def __init__(self, parent, w=210, h=170):
        self.w, self.h = w, h
        self.canvas = tk.Canvas(parent, width=w, height=h, bg=CARD,
                                highlightthickness=0, bd=0)
        self.state = "idle"
        self.t = 0.0
        self.cur_dy = self.cur_dx = 0.0
        self.blink = 0
        self.next_blink = 50
        self.hold = 0
        self.dance = 0
        self.click_n = 0
        self._png = self._load_pngs()
        if self._png:
            self.img_item = self.canvas.create_image(w // 2, h // 2,
                                                     image=self._png.get("idle"))
        else:
            self._build_pixels()
        self._tick()

    def _load_pngs(self):
        out = {}
        for st in ("idle", "excited", "happy", "sad"):
            p = resource_path("assets") / f"mascot_{st}.png"
            if p.exists():
                try:
                    out[st] = ImageTk.PhotoImage(
                        Image.open(p).convert("RGBA").resize((140, 140)))
                except Exception:
                    pass
        return out or None

    def _build_pixels(self):
        s = 7
        gw, gh = len(CAT[0]) * s, len(CAT) * s
        ox, oy = (self.w - gw) // 2, (self.h - gh) // 2 - 2
        self.eye_items = []
        for r, row in enumerate(CAT):
            for cidx, ch in enumerate(row):
                if ch == ".":
                    continue
                x, y = ox + cidx * s, oy + r * s
                it = self.canvas.create_rectangle(
                    x, y, x + s - 1, y + s - 1,
                    fill=NEON if ch == "E" else VIOLET, outline="", tags="cat")
                if ch == "E":
                    self.eye_items.append(it)
        self.canvas.create_oval(ox + 6, oy + gh - 2, ox + gw - 6, oy + gh + 8,
                                outline="", fill=NEON_DIM, tags="cat")
        self.canvas.tag_lower("cat")

    def set_state(self, st, hold=0):
        self.state, self.hold = st, hold

    def peek(self):
        if self.state == "idle":
            self.set_state("happy", hold=16)

    def click(self):
        self.click_n += 1
        if self.click_n >= 5:
            self.click_n = 0
            self.dance = 26
        self.canvas.after(1400, lambda: setattr(self, "click_n", 0))

    def start_dance(self):
        self.dance = 26

    def _tick(self):
        self.t += 0.09
        if self.hold > 0:
            self.hold -= 1
            if self.hold == 0:
                self.state = "idle"
        speed = {"excited": 3.4, "happy": 2.6, "sad": 1.1}.get(self.state, 1.6)
        amp = {"excited": 5, "happy": 4, "sad": 2}.get(self.state, 3)
        target_dy = math.sin(self.t * speed) * amp
        dx = 0.0
        if self.dance > 0:
            self.dance -= 1
            dx = random.randint(-5, 5)
            target_dy = math.sin(self.t * 6) * 7
        tag = self.img_item if self._png else "cat"
        if self._png:
            self.canvas.move(self.img_item, dx - self.cur_dx, target_dy - self.cur_dy)
            self.canvas.itemconfig(self.img_item,
                                   image=self._png.get(self.state, self._png["idle"]))
        else:
            self.canvas.move("cat", dx - self.cur_dx, target_dy - self.cur_dy)
            self.next_blink -= 1
            if self.next_blink <= 0 and self.blink == 0:
                self.blink, self.next_blink = 4, random.randint(40, 95)
            if self.blink > 0:
                self.blink -= 1
            if self.dance > 0:
                eye = random.choice((NEON, PURPLE_L, ERR, OK))
            elif self.blink > 0:
                eye = VIOLET
            elif self.state == "sad":
                eye = NEON_DIM
            else:
                eye = NEON
            for it in self.eye_items:
                self.canvas.itemconfig(it, fill=eye)
        self.cur_dx, self.cur_dy = dx, target_dy
        self.canvas.after(70, self._tick)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APP  (responsive grid layout)
# ─────────────────────────────────────────────────────────────────────────────

_Base = (ctk.CTk, TkinterDnD.DnDWrapper) if _HAS_DND else (ctk.CTk,)

class GimmeDatApp(*_Base):
    def __init__(self):
        super().__init__()
        try:
            ctk.deactivate_automatic_dpi_awareness()
        except Exception:
            pass
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        ctk.set_appearance_mode("dark")

        self.title(f"{APP_NAME} v{VERSION}")
        self.configure(fg_color=BG)
        self._set_icon()

        # state
        self.stats = Stats()
        self._dl_root = self._resolve_download_root()
        self._probe = None
        self._probe_after = None
        self._quality = "1080p"
        self._chips = []
        self._chip_reveal = 0
        self._busy = False
        self._queue = []
        self._last_file = None
        self._konami = []
        self._last_action = 0.0
        self._thumb_ref = None
        self._save_after = None
        self._music_after = None

        # remembered size (clamped to min), resizable + maximizable
        self.geometry(self.stats.geometry or DEFAULT_GEO)
        self.minsize(MIN_W, MIN_H)
        self.resizable(True, True)

        # glitch canvas behind everything
        self.bg = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg.bind("<Configure>", self._draw_scanlines)
        self.beam = self.bg.create_line(0, 0, 10, 0, fill="#1c1633", width=2)
        self.beam_y = 0

        self._build_layout()
        self._build_toast()
        self._build_help()
        self._wire_shortcuts()
        self._enable_dnd()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_configure)

        self._animate()
        self._idle_watch()
        self.after(250, self._smart_paste_on_launch)

    def _set_icon(self):
        ico = resource_path("logos") / "GimmeDat_icon.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

    # ── save location ──
    def _resolve_download_root(self) -> Path:
        """Use the user's chosen folder if set + still exists, else the default."""
        if self.stats.download_dir:
            p = Path(self.stats.download_dir)
            if p.exists() or self._safe_mkdir(p):
                return p
        return default_download_root()

    @staticmethod
    def _safe_mkdir(p: Path) -> bool:
        try:
            p.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def _pick_download_dir(self):
        """Folder-picker dialog → persists choice, updates UI label."""
        from tkinter import filedialog
        chosen = filedialog.askdirectory(
            title="Choose where GimmeDat saves videos",
            initialdir=str(self._dl_root))
        if not chosen:
            return
        p = Path(chosen)
        if not self._safe_mkdir(p):
            self._show_toast("can't write there", ERR)
            return
        self._dl_root = p
        self.stats.download_dir = str(p)
        self.stats.save()
        self._refresh_folder_label()
        self._show_toast("save folder updated ✓", OK)

    # ─────────────────── LAYOUT ───────────────────
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)          # main grows
        self.grid_columnconfigure(1, weight=0, minsize=276)
        self.grid_rowconfigure(1, weight=1)             # content row grows

        self._build_header()
        self._build_main()
        self._build_sidebar()
        self._build_footer()

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color=BORDER, **kw)

    # ── header ──
    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 6))
        h.grid_columnconfigure(2, weight=1)

        logo = ctk.CTkFrame(h, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(logo, text="Gimme", font=(F_DISP, 26, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(logo, text="Dat", font=(F_DISP, 26, "bold"),
                     text_color=NEON).pack(side="left")
        ctk.CTkLabel(h, text=f"v{VERSION}", font=(F_MONO, 11),
                     text_color=FAINT).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._music_on = ENABLE_MUSIC
        self.music_btn = ctk.CTkButton(h, text="♫ music: off", width=124, height=30,
                                       fg_color=CARD2, hover_color=GLOW, text_color=MUTED,
                                       font=(F_MONO, 11, "bold"), corner_radius=8,
                                       command=self._toggle_music)
        self.music_btn.grid(row=0, column=3, padx=6)
        ctk.CTkButton(h, text="?", width=34, height=30, fg_color=CARD2,
                      hover_color=GLOW, text_color=NEON, font=(F_MONO, 13, "bold"),
                      corner_radius=8, command=self._toggle_help).grid(row=0, column=4)
        self._set_music_label()

    # ── main column ──
    def _build_main(self):
        # scrollable so content never clips at small window heights
        m = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0,
                                   scrollbar_button_color=GLOW,
                                   scrollbar_button_hover_color=PURPLE)
        m.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=4)
        m.grid_columnconfigure(0, weight=1)

        # url entry
        self.url_entry = ctk.CTkEntry(
            m, placeholder_text="paste or drop a link…", height=46, corner_radius=10,
            fg_color=PANEL, border_color=BORDER, text_color=TEXT,
            placeholder_text_color=FAINT, font=(F_MONO, 13))
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.bind("<KeyRelease>", self._on_url_change)

        # detected row (icon + text)
        det = ctk.CTkFrame(m, fg_color="transparent")
        det.grid(row=1, column=0, sticky="ew", pady=(6, 2))
        self._det_icon_holder = ctk.CTkFrame(det, fg_color="transparent", width=24, height=24)
        self._det_icon_holder.pack(side="left")
        self._det_icon_holder.pack_propagate(False)
        self._det_icon = None
        self.detected_lbl = ctk.CTkLabel(det, text="", font=(F_MONO, 11, "bold"),
                                         text_color=NEON)
        self.detected_lbl.pack(side="left", padx=6)

        # buttons row
        br = ctk.CTkFrame(m, fg_color="transparent")
        br.grid(row=2, column=0, sticky="ew", pady=(2, 8))
        br.grid_columnconfigure(0, weight=1)
        self.grab_btn = ctk.CTkButton(br, text="GRAB IT", height=46, corner_radius=12,
                                      fg_color=PURPLE, hover_color=VIOLET, text_color="white",
                                      font=(F_DISP, 15, "bold"), command=self._grab_clicked)
        self.grab_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.paste_btn = ctk.CTkButton(br, text="⚡ paste & grab", width=200, height=46,
                                       corner_radius=12, fg_color=CARD2, hover_color=GLOW,
                                       text_color=NEON, border_width=1, border_color=GLOW,
                                       font=(F_MONO, 12, "bold"), command=self._paste_and_grab)
        self.paste_btn.grid(row=0, column=1)

        # info card (hidden until probe)
        self.info_card = self._card(m)
        self.info_card.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.info_card.grid_columnconfigure(1, weight=1)
        self.thumb_lbl = ctk.CTkLabel(self.info_card, text="", width=160, height=90,
                                      fg_color=PANEL, corner_radius=8)
        self.thumb_lbl.grid(row=0, column=0, rowspan=3, padx=12, pady=12)
        self.info_title = ctk.CTkLabel(self.info_card, text="", font=(F_MONO, 13, "bold"),
                                       text_color=TEXT, anchor="w", justify="left")
        self.info_title.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(14, 0))
        self.info_chan = ctk.CTkLabel(self.info_card, text="", font=(F_MONO, 11),
                                      text_color=MUTED, anchor="w")
        self.info_chan.grid(row=1, column=1, sticky="ew", padx=(0, 12))
        self.info_dur = ctk.CTkLabel(self.info_card, text="", font=(F_MONO, 11, "bold"),
                                     text_color=NEON, anchor="w")
        self.info_dur.grid(row=2, column=1, sticky="w", padx=(0, 12), pady=(0, 12))
        self.info_title.bind("<Configure>",
                             lambda e: self.info_title.configure(wraplength=max(120, e.width - 10)))
        self.info_card.grid_remove()

        # empty state (shown when no probe)
        self.empty_lbl = ctk.CTkLabel(
            m, text="◇  paste, drop, or ⚡ a link to begin", font=(F_MONO, 13),
            text_color=FAINT)
        self.empty_lbl.grid(row=3, column=0, sticky="ew", pady=18)

        # quality section (hidden until probe)
        self.qbox = ctk.CTkFrame(m, fg_color="transparent")
        self.qbox.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.qbox.grid_columnconfigure(0, weight=1)
        qhead = ctk.CTkFrame(self.qbox, fg_color="transparent")
        qhead.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(qhead, text="QUALITY", font=(F_MONO, 10, "bold"),
                     text_color=FAINT).pack(side="left")
        self.qload = ctk.CTkLabel(qhead, text="", font=(F_MONO, 10), text_color=NEON)
        self.qload.pack(side="right")
        self.chips_box = ctk.CTkFrame(self.qbox, fg_color="transparent")
        self.chips_box.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.chips_box.bind("<Configure>", lambda e: self._rewrap_chips())
        self.qbox.grid_remove()

        # progress card
        pc = self._card(m)
        pc.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        pc.grid_columnconfigure(0, weight=1)
        self.status_lbl = ctk.CTkLabel(pc, text="waiting for a link…", font=(F_MONO, 12),
                                       text_color=FAINT, anchor="w")
        self.status_lbl.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        self.pbar = ctk.CTkProgressBar(pc, height=8, corner_radius=99,
                                       fg_color=PANEL, progress_color=NEON)
        self.pbar.set(0)
        self.pbar.grid(row=1, column=0, sticky="ew", padx=14)
        self.detail_lbl = ctk.CTkLabel(pc, text="", font=(F_MONO, 10),
                                       text_color=FAINT, anchor="w")
        self.detail_lbl.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 12))

        # last-grab card
        ctk.CTkLabel(m, text="LAST GRAB", font=(F_MONO, 10, "bold"),
                     text_color=FAINT).grid(row=7, column=0, sticky="w", pady=(4, 4))
        lc = self._card(m)
        lc.grid(row=8, column=0, sticky="ew")
        lc.grid_columnconfigure(1, weight=1)
        self.last_icon_holder = ctk.CTkFrame(lc, fg_color="transparent", width=24, height=24)
        self.last_icon_holder.grid(row=0, column=0, rowspan=2, padx=(14, 6), pady=14)
        self.last_icon_holder.grid_propagate(False)
        self._last_icon = None
        self.last_title = ctk.CTkLabel(lc, text="nothing yet — grab something",
                                       font=(F_MONO, 12, "bold"), text_color=MUTED, anchor="w")
        self.last_title.grid(row=0, column=1, sticky="ew", pady=(12, 0))
        self.last_meta = ctk.CTkLabel(lc, text="", font=(F_MONO, 10),
                                      text_color=FAINT, anchor="w")
        self.last_meta.grid(row=1, column=1, sticky="ew", pady=(0, 12))
        bb = ctk.CTkFrame(lc, fg_color="transparent")
        bb.grid(row=0, column=2, rowspan=2, padx=12)
        ctk.CTkButton(bb, text="open folder", width=100, height=30, fg_color=CARD2,
                      hover_color=GLOW, text_color=MUTED, font=(F_MONO, 11),
                      corner_radius=8, command=self._open_folder).pack(pady=2)
        ctk.CTkButton(bb, text="open file", width=100, height=30, fg_color=PURPLE,
                      hover_color=VIOLET, text_color="white", font=(F_MONO, 11),
                      corner_radius=8, command=self._open_file).pack(pady=2)

        # queue strip
        self.queue_lbl = ctk.CTkLabel(m, text="", font=(F_MONO, 10, "bold"),
                                      text_color=NEON, anchor="w")
        self.queue_lbl.grid(row=9, column=0, sticky="w", pady=(6, 0))

        self._render_last()

    # ── sidebar ──
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color="transparent")
        sb.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=4)
        sb.grid_columnconfigure(0, weight=1)

        mc = self._card(sb)
        mc.grid(row=0, column=0, sticky="ew")
        self.mascot = Mascot(mc, w=244, h=180)
        self.mascot.canvas.pack(padx=6, pady=6)
        self.mascot.canvas.bind("<Button-1>", lambda e: self.mascot.click())

        st = self._card(sb)
        st.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ctk.CTkLabel(st, text="STATS", font=(F_MONO, 9, "bold"),
                     text_color=FAINT).pack(anchor="w", padx=14, pady=(12, 2))
        self.stats_a = ctk.CTkLabel(st, text="", font=(F_MONO, 14, "bold"), text_color=TEXT)
        self.stats_a.pack(anchor="w", padx=14)
        self.stats_b = ctk.CTkLabel(st, text="", font=(F_MONO, 12, "bold"), text_color=NEON)
        self.stats_b.pack(anchor="w", padx=14, pady=(0, 12))

        # save-folder card
        sf = self._card(sb)
        sf.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        sf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(sf, text="SAVE TO", font=(F_MONO, 9, "bold"),
                     text_color=FAINT).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))
        self.folder_lbl = ctk.CTkLabel(sf, text="", font=(F_MONO, 10),
                                       text_color=TEXT, anchor="w",
                                       wraplength=240, justify="left")
        self.folder_lbl.grid(row=1, column=0, sticky="ew", padx=14)
        ctk.CTkButton(sf, text="📁 change folder", height=32, fg_color=CARD2,
                      hover_color=GLOW, text_color=NEON, font=(F_MONO, 11, "bold"),
                      corner_radius=8, command=self._pick_download_dir
                      ).grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 12))

        ctk.CTkButton(sb, text="♥ buy me a coffee", height=40, fg_color=PURPLE,
                      hover_color=VIOLET, font=(F_MONO, 12, "bold"), corner_radius=10,
                      command=lambda: webbrowser.open(BUYMEACOFFEE_URL)
                      ).grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ctk.CTkButton(sb, text="PayPal", height=38, fg_color=CARD2, hover_color=GLOW,
                      text_color=NEON, font=(F_MONO, 12, "bold"), corner_radius=10,
                      command=lambda: webbrowser.open(PAYPAL_URL)
                      ).grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ctk.CTkLabel(sb, text="click the cat 5× 👀", font=(F_MONO, 9),
                     text_color=FAINT).grid(row=5, column=0, pady=(10, 0))
        self._refresh_stats()
        self._refresh_folder_label()

    def _refresh_folder_label(self):
        p = str(self._dl_root)
        if len(p) > 40:
            p = "…" + p[-39:]
        self.folder_lbl.configure(text=p)

    # ── footer ──
    def _build_footer(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        ctk.CTkLabel(f, text=f"made by Kaiden  —  © 2026 Kaiden. All rights reserved.  ·  v{VERSION}",
                     font=(F_MONO, 9), text_color=FAINT).pack()

    # ─────────────────── GLITCH ANIM ───────────────────
    def _draw_scanlines(self, event=None):
        self.bg.delete("scan")
        w = self.bg.winfo_width()
        h = self.bg.winfo_height()
        for y in range(0, h, 4):
            self.bg.create_line(0, y, w, y, fill="#0c0a14", tags="scan")
        self.bg.tag_lower("scan")

    def _animate(self):
        h = self.bg.winfo_height()
        w = self.bg.winfo_width()
        if h > 1:
            self.beam_y = (self.beam_y + 4) % (h + 30)
            self.bg.coords(self.beam, 0, self.beam_y, w, self.beam_y)
            if random.random() < 0.06:
                gy, gx = random.randint(0, h), random.randint(0, max(1, w - 150))
                bar = self.bg.create_rectangle(gx, gy, gx + random.randint(50, 150),
                                               gy + random.randint(2, 5),
                                               outline=random.choice((NEON, PURPLE_L)),
                                               fill="", tags="fx")
                self.bg.after(130, lambda b=bar: self.bg.delete(b))
        self.after(90, self._animate)

    # ─────────────────── RESIZE / CLOSE ───────────────────
    def _on_configure(self, event=None):
        if self._save_after:
            self.after_cancel(self._save_after)
        self._save_after = self.after(600, self._save_geo)

    def _save_geo(self):
        try:
            if self.state() == "normal":
                self.stats.geometry = self.geometry()
                self.stats.save()
        except Exception:
            pass

    def _on_close(self):
        self._stop_music()
        self._save_geo()
        self.destroy()

    # ─────────────────── URL CHANGE + PROBE ───────────────────
    def _on_url_change(self, event=None):
        self._mark_action()
        url = self.url_entry.get().strip()
        plat = detect_platform(url)
        self._set_detected(plat)
        if self._probe_after:
            self.after_cancel(self._probe_after)
        self._probe = None
        if not url:
            self._hide_quality(reset_empty=True)
        if plat and url.startswith("http"):
            self._probe_after = self.after(600, lambda: self._do_probe(url))

    def _set_detected(self, plat):
        for w in self._det_icon_holder.winfo_children():
            w.destroy()
        if plat:
            self._det_icon = make_icon(self._det_icon_holder, plat, 22, bg=BG)
            self._det_icon.pack()
            self.detected_lbl.configure(text=f"detected: {PLATFORMS[plat]['label']}")
        else:
            self.detected_lbl.configure(text="")

    def _do_probe(self, url):
        self.empty_lbl.grid_remove()
        self.qbox.grid()
        self.qload.configure(text="reading formats…")
        for c in self.chips_box.winfo_children():
            c.destroy()
        self._chips = []
        self._set_status("scanning formats…", NEON)
        threading.Thread(target=self._probe_thread, args=(url,), daemon=True).start()

    def _probe_thread(self, url):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                   "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            heights, has_audio, by_h, best_audio = [], False, {}, 0
            for f in info.get("formats", []):
                sz = f.get("filesize") or f.get("filesize_approx") or 0
                if f.get("vcodec") not in (None, "none") and f.get("height"):
                    heights.append(f["height"])
                    if sz:
                        by_h[f["height"]] = max(by_h.get(f["height"], 0), sz)
                if f.get("acodec") not in (None, "none"):
                    has_audio = True
                    if f.get("vcodec") in (None, "none") and sz:
                        best_audio = max(best_audio, sz)
            max_h = max(heights) if heights else None
            sizes = {}
            for name, v in QUALITY_TIERS:
                if v == "audio":
                    dur = info.get("duration")
                    sizes[name] = int(dur * 24000) if dur else (best_audio or 0)
                else:
                    cand = [hh for hh in by_h if hh <= v]
                    sizes[name] = (by_h[max(cand)] + best_audio) if cand else 0
            self._probe = {
                "url": url, "title": (info.get("title") or "unknown")[:90],
                "channel": info.get("uploader") or info.get("channel") or "",
                "duration": fmt_duration(info.get("duration")),
                "thumb": info.get("thumbnail"),
                "max_h": max_h, "has_audio": has_audio, "sizes": sizes,
                "plat": detect_platform(url),
            }
            self.after(0, self._on_probe_done)
        except Exception as e:
            self.after(0, self._probe_failed, clean_error(str(e)))

    def _probe_failed(self, msg):
        self.qload.configure(text="")
        self._hide_quality(reset_empty=True)
        self._set_status(msg, ERR)

    def _on_probe_done(self):
        p = self._probe
        if not p:
            return
        self.info_card.grid()
        self.qbox.grid()                 # ensure quality section is visible
        self.empty_lbl.grid_remove()
        self.info_title.configure(text=p["title"])
        self.info_chan.configure(text=("by " + p["channel"]) if p["channel"] else "")
        self.info_dur.configure(text=("⏱ " + p["duration"]) if p["duration"] else "")
        self.qload.configure(text="")
        self._populate_chips(p)
        self._set_status("ready — pick a quality & grab it", OK)
        if p.get("thumb"):
            threading.Thread(target=self._fetch_thumb, args=(p["thumb"],), daemon=True).start()

    def _fetch_thumb(self, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=8).read()
            img = Image.open(BytesIO(data)).convert("RGB")
            img.thumbnail((160, 90))
            self.after(0, self._set_thumb, img)
        except Exception:
            pass

    def _set_thumb(self, img):
        self._thumb_ref = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.thumb_lbl.configure(image=self._thumb_ref, text="")

    # ─────────────────── QUALITY CHIPS (responsive + animated in) ───────────────────
    def _hide_quality(self, reset_empty=False):
        self.qbox.grid_remove()
        self.info_card.grid_remove()
        if reset_empty:
            self.empty_lbl.grid()
        for c in self.chips_box.winfo_children():
            c.destroy()
        self._chips = []

    def _populate_chips(self, p):
        best = None
        self._chips = []
        for name, v in QUALITY_TIERS:
            if v == "audio":
                on = bool(p["has_audio"])
            elif p["max_h"] is None:
                on = v <= 1080
            else:
                on = p["max_h"] >= v
            sz = p["sizes"].get(name)
            txt = name + (f"\n~{human_size(sz)}" if (on and sz) else "\n—" if on else "\nn/a")
            btn = ctk.CTkButton(self.chips_box, text=txt, height=46, width=150,
                                corner_radius=10, font=(F_MONO, 12, "bold"),
                                fg_color=PANEL, hover_color=GLOW,
                                text_color=MUTED if on else "#3b3559",
                                border_width=1, border_color=BORDER,
                                state="normal" if on else "disabled",
                                command=lambda n=name: self._pick_chip(n))
            btn._tier = name
            btn._on = on
            self._chips.append(btn)
            if on and v != "audio" and best is None:
                best = name
        # default selection
        if not self._tier_on("1080p") or self._quality not in [c._tier for c in self._chips if c._on]:
            self._quality = "1080p" if self._tier_on("1080p") else (best or ("MP3" if p["has_audio"] else self._quality))
        # animate in (staggered reveal)
        self._chip_reveal = 0
        self._reveal_next()

    def _tier_on(self, tier):
        for c in self._chips:
            if c._tier == tier:
                return c._on
        return False

    def _reveal_next(self):
        if self._chip_reveal >= len(self._chips):
            self._refresh_chips()
            return
        self._chip_reveal += 1
        self._rewrap_chips()
        self._refresh_chips()
        self.after(35, self._reveal_next)

    def _rewrap_chips(self):
        if not self._chips:
            return
        w = self.chips_box.winfo_width() or 560
        cols = max(2, min(len(self._chips), w // 162))
        shown = self._chips[:self._chip_reveal] if self._chip_reveal else self._chips
        for i, btn in enumerate(self._chips):
            btn.grid_forget()
        for i in range(self.chips_box.grid_size()[0]):
            self.chips_box.grid_columnconfigure(i, weight=0)
        for i, btn in enumerate(shown):
            r, c = divmod(i, cols)
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
        for c in range(cols):
            self.chips_box.grid_columnconfigure(c, weight=1)

    def _pick_chip(self, name):
        self._quality = name
        self._refresh_chips()
        self._mark_action()

    def _refresh_chips(self):
        for btn in self._chips:
            if not btn._on:
                continue
            if btn._tier == self._quality:
                btn.configure(fg_color=PURPLE, text_color="white", border_color=NEON)
            else:
                btn.configure(fg_color=PANEL, text_color=MUTED, border_color=BORDER)

    # ─────────────────── DOWNLOAD FLOW ───────────────────
    def _grab_clicked(self):
        self._mark_action()
        if self._help_shown:
            self._toggle_help()
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("yo, paste a link first", ERR)
            return
        if not detect_platform(url):
            self._set_status("that link isn't supported", ERR)
            return
        self._enqueue(url, auto=False)

    def _paste_and_grab(self):
        self._mark_action()
        urls = find_urls(self._read_clipboard())
        if not urls:
            self._show_toast("no video link in clipboard", ERR)
            return
        if len(urls) == 1:
            self._load_url(urls[0])
        for u in urls:
            self._enqueue(u, auto=True, quiet=True)
        self._show_toast(f"queued {len(urls)} ⚡" if len(urls) > 1 else "grabbing ⚡", NEON)

    def _paste_detect(self):
        urls = find_urls(self._read_clipboard())
        if urls:
            self._load_url(urls[0])

    def _read_clipboard(self):
        try:
            return self.clipboard_get()
        except Exception:
            return ""

    def _load_url(self, url):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self._on_url_change()

    def _clear(self):
        self.url_entry.delete(0, "end")
        self._on_url_change()
        self._set_status("cleared", MUTED)
        self._hide_quality(reset_empty=True)

    def _smart_paste_on_launch(self):
        urls = find_urls(self._read_clipboard())
        if urls and not self.url_entry.get().strip():
            self.detected_lbl.configure(text="📋 link in clipboard — Ctrl+V to load")

    def _enqueue(self, url, auto, quiet=False):
        plat = detect_platform(url)
        if not plat:
            return
        self._queue.append((url, plat, auto))
        self._render_queue()
        self._process_queue()

    def _process_queue(self):
        if self._busy or not self._queue:
            return
        url, plat, auto = self._queue.pop(0)
        self._render_queue()
        self._busy = True
        self.grab_btn.configure(state="disabled", text="GRABBING…")
        self.mascot.set_state("excited")
        self.pbar.set(0)
        self._set_status(f"connecting to {PLATFORMS[plat]['label']}…", NEON)
        threading.Thread(target=self._download_thread, args=(url, plat, auto),
                         daemon=True).start()

    def _render_queue(self):
        n = len(self._queue)
        self.queue_lbl.configure(text=(f"⏳ queue: {n} waiting" if n else ""))

    def _build_opts(self, out_dir, ffmpeg, quality):
        v = dict(QUALITY_TIERS)[quality]
        opts = {"outtmpl": str(out_dir / "%(title).80s.%(ext)s"),
                "restrictfilenames": True, "windowsfilenames": True,
                "quiet": True, "no_warnings": True,
                "progress_hooks": [self._yt_hook],
                "postprocessor_hooks": [self._pp_hook]}
        if ffmpeg:
            opts["ffmpeg_location"] = ffmpeg
        if v == "audio":
            opts["format"] = "bestaudio/best"
            if ffmpeg:
                opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                           "preferredcodec": "mp3", "preferredquality": "192"}]
        else:
            if ffmpeg:
                opts["format"] = (f"bestvideo[height<={v}][ext=mp4]+bestaudio[ext=m4a]/"
                                  f"bestvideo[height<={v}]+bestaudio/best[height<={v}]/best")
                opts["merge_output_format"] = "mp4"
            else:
                opts["format"] = f"best[height<={v}][ext=mp4]/best[height<={v}]/best"
        return opts

    def _download_thread(self, url, plat, auto):
        # save straight into the user's chosen folder, no platform subdirs
        out_dir = self._dl_root
        out_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = get_ffmpeg()
        self._last_file = None
        try:
            self.after(0, self._set_status, "fetching stream…", NEON)
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                   "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            heights = [f["height"] for f in info.get("formats", [])
                       if f.get("vcodec") not in (None, "none") and f.get("height")]
            has_audio = any(f.get("acodec") not in (None, "none") for f in info.get("formats", []))
            max_h = max(heights) if heights else None
            quality = self._choose_quality(auto, max_h, has_audio)
            title = (info.get("title") or "unknown")[:70]
            self.after(0, self._set_status, f"snatching: {title}", NEON)
            opts = self._build_opts(out_dir, ffmpeg, quality)
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    ydl.download([url])
                except yt_dlp.utils.DownloadError as e:
                    if "Requested format is not available" in str(e):
                        opts["format"] = "best"
                        opts.pop("merge_output_format", None)
                        with yt_dlp.YoutubeDL(opts) as y2:
                            y2.download([url])
                    else:
                        raise
            size = os.path.getsize(self._last_file) if self._last_file and os.path.exists(self._last_file) else 0
            self.after(0, self._on_done, title, plat, quality, size)
        except Exception as e:
            self.after(0, self._on_error, clean_error(str(e)))

    def _choose_quality(self, auto, max_h, has_audio):
        if not auto:
            v = dict(QUALITY_TIERS).get(self._quality)
            if v == "audio":
                return "MP3" if has_audio else self._quality
            if v and (max_h is None or max_h >= v):
                return self._quality
        for name, v in QUALITY_TIERS:
            if v == "audio":
                continue
            if v <= 1080 and (max_h is None or max_h >= v):
                return name
        return "MP3" if has_audio else "720p"

    def _yt_hook(self, d):
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "").strip().replace("%", "")
            spd = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            try:
                self.after(0, self.pbar.set, float(pct) / 100)
            except Exception:
                pass
            self.after(0, self._set_detail, f"{pct}%   ·   {spd}   ·   eta {eta}")
            self.after(0, self._set_status, "snatching stream…", NEON)
        elif d["status"] == "finished":
            self._last_file = d.get("filename")
            self.after(0, self._set_status, "stream done — processing…", NEON)

    def _pp_hook(self, d):
        if d.get("status") == "finished":
            fp = (d.get("info_dict") or {}).get("filepath")
            if fp:
                self._last_file = fp
        if d.get("status") != "started":
            return
        pp = d.get("postprocessor", "")
        if "ExtractAudio" in pp:
            self.after(0, self._set_status, "converting to mp3…", NEON)
        elif "Merger" in pp or "FFmpeg" in pp:
            self.after(0, self._set_status, "merging video + audio…", NEON)

    def _on_done(self, title, plat, quality, size):
        self._busy = False
        self.pbar.set(1)
        self.mascot.set_state("happy", hold=22)
        self._set_status("done fr ✓", OK)
        self._set_detail(self._last_file or "")
        self.grab_btn.configure(state="normal", text="GRAB IT")
        self.stats.add(size, {"title": title, "platform": plat, "quality": quality,
                              "size": human_size(size), "path": self._last_file})
        self._render_last()
        self._refresh_stats()
        self._show_toast("saved ✓", OK)
        self.after(300, self._process_queue)

    def _on_error(self, msg):
        self._busy = False
        self.mascot.set_state("sad", hold=28)
        self._set_status(msg, ERR)
        self.pbar.set(0)
        self.grab_btn.configure(state="normal", text="GRAB IT")
        self._show_toast(msg, ERR)
        self.after(300, self._process_queue)

    # ─────────────────── small setters ───────────────────
    def _set_status(self, msg, color=TEXT):
        self.status_lbl.configure(text=msg, text_color=color)

    def _set_detail(self, msg):
        self.detail_lbl.configure(text=(msg or "")[:90])

    def _refresh_stats(self):
        self.stats_a.configure(text=f"{self.stats.count} files")
        self.stats_b.configure(text=f"{self.stats.bytes / 1e9:.2f} GB saved")

    def _render_last(self):
        last = self.stats.last
        if not last:
            return
        for w in self.last_icon_holder.winfo_children():
            w.destroy()
        self._last_icon = make_icon(self.last_icon_holder, last.get("platform", ""), 22)
        self._last_icon.pack()
        self.last_title.configure(text=last["title"], text_color=TEXT)
        meta = "  ·  ".join(x for x in (PLATFORMS.get(last["platform"], {}).get("label"),
                                        last.get("quality"), last.get("size")) if x)
        self.last_meta.configure(text=meta)

    # ─────────────────── toast / help ───────────────────
    def _build_toast(self):
        self.toast = ctk.CTkFrame(self, fg_color=CARD2, corner_radius=12,
                                  border_width=1, border_color=NEON)
        self.toast_lbl = ctk.CTkLabel(self.toast, text="", text_color=TEXT,
                                      font=(F_MONO, 12, "bold"))
        self.toast_lbl.pack(padx=16, pady=10)

    def _show_toast(self, text, color=NEON):
        self.toast.configure(border_color=color)
        self.toast_lbl.configure(text=text)
        self.toast.place(relx=1.0, rely=1.0, x=-16, y=-16, anchor="se")
        self.toast.lift()
        if hasattr(self, "_toast_after") and self._toast_after:
            self.after_cancel(self._toast_after)
        self._toast_after = self.after(2400, self.toast.place_forget)

    def _build_help(self):
        self.help_box = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14,
                                     border_width=1, border_color=GLOW)
        ctk.CTkLabel(self.help_box, justify="left", text_color=TEXT, font=(F_MONO, 12),
                     text=("KEYBOARD\n\nEnter      grab\nCtrl+V     paste + detect\n"
                           "Esc        clear\n\ndrag a link onto the window\n"
                           "click the cat 5× 👀")).pack(padx=20, pady=16)
        self._help_shown = False

    def _toggle_help(self):
        if self._help_shown:
            self.help_box.place_forget()
        else:
            self.help_box.place(relx=0.5, rely=0.5, anchor="center")
            self.help_box.lift()
        self._help_shown = not self._help_shown

    # ─────────────────── shortcuts / dnd / idle ───────────────────
    def _wire_shortcuts(self):
        self.bind("<Return>", lambda e: self._grab_clicked())
        self.bind("<Escape>", lambda e: self._clear())
        self.bind("<Control-v>", lambda e: self._paste_detect())
        self.bind("<Key>", self._konami_key)

    def _enable_dnd(self):
        self._dnd = False
        if not _HAS_DND:
            return
        try:
            self.TkdndVersion = TkinterDnD._require(self)
            self.drop_target_register(DND_FILES, DND_TEXT)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self._dnd = True
        except Exception:
            self._dnd = False

    def _on_drop(self, event):
        urls = find_urls((event.data or "").strip().strip("{}"))
        if urls:
            self._load_url(urls[0])
            self._show_toast("link dropped ✓", NEON)
        else:
            self._show_toast("no video link in that drop", ERR)

    def _idle_watch(self):
        import time
        if time.time() - self._last_action > 30 and not self._busy:
            self.mascot.peek()
            self._last_action = time.time()
        self.after(5000, self._idle_watch)

    def _mark_action(self):
        import time
        self._last_action = time.time()

    def _konami_key(self, event):
        seq = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        self._konami.append(event.keysym)
        self._konami = self._konami[-len(seq):]
        if self._konami == seq:
            self.mascot.start_dance()
            self._show_toast("🐱 glitch dance!", NEON)

    # ─────────────────── background music (MCI — no extra deps) ───────────────────
    def _mci(self, cmd):
        if _HAS_MCI:
            ctypes.windll.winmm.mciSendStringW(cmd, None, 0, None)

    def _toggle_music(self):
        self._music_on = not self._music_on
        if self._music_on:
            self._start_music()
        else:
            self._stop_music()
        self._set_music_label()

    def _set_music_label(self):
        on = self._music_on
        self.music_btn.configure(text="♫ music: on" if on else "♫ music: off",
                                 fg_color=PURPLE if on else CARD2,
                                 text_color="white" if on else MUTED)

    def _start_music(self):
        path = resource_path(BGM_FILE)
        if not (_HAS_MCI and path.exists()):
            self._music_on = False
            self._set_music_label()
            self._show_toast("no music file bundled", ERR)
            return
        try:
            self._mci("close gimmebgm")            # reset if already open
            self._mci(f'open "{path}" type mpegvideo alias gimmebgm')
            self._mci("play gimmebgm from 0")
        except Exception:
            self._music_on = False
            self._set_music_label()
            self._show_toast("couldn't start music", ERR)
            return
        self._music_loop()

    def _music_loop(self):
        # MCI won't reliably auto-loop mp3, so poll and replay when it ends
        if not (self._music_on and _HAS_MCI):
            return
        try:
            buf = ctypes.create_unicode_buffer(64)
            ctypes.windll.winmm.mciSendStringW("status gimmebgm mode", buf, 64, None)
            if buf.value == "stopped":
                self._mci("play gimmebgm from 0")
        except Exception:
            pass
        self._music_after = self.after(700, self._music_loop)

    def _stop_music(self):
        if self._music_after:
            self.after_cancel(self._music_after)
            self._music_after = None
        try:
            self._mci("stop gimmebgm")
            self._mci("close gimmebgm")
        except Exception:
            pass

    # ─────────────────── open folder / file ───────────────────
    def _open_folder(self):
        import subprocess, platform
        last = self.stats.last
        path = os.path.dirname(last["path"]) if (last and last.get("path")) else str(self._dl_root)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            self._show_toast("couldn't open folder", ERR)

    def _open_file(self):
        path = self.stats.last.get("path") if self.stats.last else None
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception:
                self._show_toast("couldn't open file", ERR)
        else:
            self._show_toast("no file yet", ERR)


if __name__ == "__main__":
    app = GimmeDatApp()
    app.mainloop()
