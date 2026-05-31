<div align="center">

# GimmeDat

### snatch any video · hd · free forever · no cap

A clean **cyberpunk-glitch** desktop video downloader for 12+ platforms (and 1000+ sites under the hood).
Paste, drop, or one-tap a link → it grabs the video.

![License](https://img.shields.io/badge/license-GPL--3.0-7c3aed?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows-22d3ee?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11%2B-a78bfa?style=for-the-badge)
![Version](https://img.shields.io/badge/version-1.0-8b5cf6?style=for-the-badge)

<img src="screenshots/probed.png" width="780" alt="GimmeDat main UI">

</div>

---

## ✨ Features

- 🎬 **12+ platforms** — YouTube, TikTok, Instagram, Pinterest, Twitter/X, Facebook, Reddit, SoundCloud, Vimeo, Twitch, Dailymotion, Bilibili — plus 1000+ more.
- 📁 **Pick your save folder** — change where videos save anytime; remembered between sessions.
- 🎯 **Smart quality detection** — probes the link and lights up **only the resolutions that actually exist** (4K → 240p + MP3), each with a **file-size estimate**. No fake upscaling.
- 📥 **Three ways to load a link** — paste, **drag & drop** a link/tab onto the window, or **⚡ paste & grab** (one-tap clipboard → download).
- 🖼️ **Rich preview** — thumbnail, title, channel, and duration before you grab.
- 🎵 **HD done right** — best video + audio merged to MP4 with **bundled ffmpeg** (no separate install); or 192 kbps MP3.
- 🐱 **Pixel cyber-cat mascot** — idles, blinks, reacts to downloads, hides an easter egg.
- 🎶 **Background music** — looping 8-bit soundtrack (toggle, off by default).
- 🧠 **Quality-of-life** — clipboard queue, smart filenames, live GB stats, toast notifications, keyboard shortcuts, graceful error messages.
- 🖥️ **Resizable & responsive** — drag/maximize and the layout reflows; the quality grid re-wraps its columns.
- 💜 **Free forever.**

---

## 📸 Screenshots

| Idle | After pasting a link | Resized / responsive |
|:---:|:---:|:---:|
| <img src="screenshots/idle.png" width="270"> | <img src="screenshots/probed.png" width="270"> | <img src="screenshots/resized.png" width="270"> |

---

## ⬇️ Download (no install)

Grab the latest **`GimmeDat.exe`** from the [**Releases**](../../releases) page and double-click it. Windows only. No Python needed.

> First launch takes a few seconds to unpack. Windows SmartScreen may warn on an unsigned exe — click *More info → Run anyway*.

---

## 🛠️ Run / build from source

Requires **Python 3.11+** on Windows.

```bash
pip install -r requirements.txt
python GimmeDat_source.py          # run directly
```

Build the standalone `.exe`:

```bash
pyinstaller --onefile --noconsole --name GimmeDat ^
  --icon="logos\GimmeDat_icon.ico" ^
  --add-data="logos;logos" --add-data="assets;assets" ^
  --collect-all imageio_ffmpeg --collect-all tkinterdnd2 ^
  GimmeDat_source.py
```

Output → `dist\GimmeDat.exe`. See [`BUILD.md`](BUILD.md) for the full guide.

---

## ⚙️ How it works

1. **Detect** the platform from the URL (regex).
2. **Probe** the URL (no download) → title, channel, duration, thumbnail, real stream heights + size estimates.
3. **Select format** — `bestvideo[height<=h] + bestaudio` merged to MP4, or `bestaudio` → MP3.
4. **Merge** with bundled **ffmpeg** (this is why HD works — without it you'd be capped at 360p).
5. **Save** into `~/Downloads/GimmeDat Downloads/<Platform>/` and update stats.

> **Honest note on motion:** this is a tkinter app. The glitch/mascot run at ~15fps by *moving* canvas items (not redrawing) — clean and light, **not** 60fps. For richer motion graphics you'd want a web (Tauri/Electron) or Qt/QML stack.

---

## 🧰 Tech stack

`customtkinter` · `tkinter.Canvas` · `Pillow` · `imageio-ffmpeg` · `tkinterdnd2` · `ctypes` (winmm/MCI for music) · `pyinstaller` + open-source video-extraction libraries

---

## 📜 License & copyright

**Copyright © 2026 Kaiden.**

GimmeDat is licensed under the **[GNU General Public License v3.0](LICENSE)**.

You are free to use, study, share, and modify it — but **any distributed copy or derivative must remain open source under the GPL and must credit the original author (Kaiden).** It may **not** be relicensed, closed-sourced, or sold as proprietary software. See [`LICENSE`](LICENSE) for the full terms.

---

<div align="center">

**made by Kaiden** · © 2026 Kaiden

*If GimmeDat saved you time, consider supporting it* 💜
[☕ Buy me a coffee](https://buymeacoffee.com/ridhakaiden) · [PayPal](https://paypal.me/1mkaiden)

</div>
