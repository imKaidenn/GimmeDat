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
- 🖼 **Images too** — paste any image link (Imgur, Reddit, Twitter/X, Pinterest, Instagram CDN, Unsplash…) and GimmeDat grabs the **highest-quality** version, bypassing hotlink-blocking sites.
- 📁 **Pick your save folder** — change where videos save anytime; remembered between sessions. Files save flat — no per-platform subfolders.
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

| Idle | Video link probed | Image link detected | Resized / responsive |
|:---:|:---:|:---:|:---:|
| <img src="screenshots/idle.png" width="200"> | <img src="screenshots/probed.png" width="200"> | <img src="screenshots/image.png" width="200"> | <img src="screenshots/resized.png" width="200"> |

---

## ⬇️ Download (no install)

Grab the latest **`GimmeDat.exe`** from the [**Releases**](../../releases) page and double-click it. Windows only. No Python needed.

---

## 🛡️ "Windows protected your PC" — is this safe?

**Yes.** That warning ("**Windows protected your PC** · Unknown publisher") shows up for **every** unsigned `.exe` on the internet — including from huge well-known indie devs. It is *not* a "this app is suspicious" signal; it's a "this app hasn't paid Microsoft for a code-signing certificate" signal. The reasons GimmeDat is unsigned right now: a signing cert costs ~$200–700/year, which we'd rather not pass on to users of a free-forever tool.

**How to run it safely:**
1. Click **More info** on the warning
2. Click **Run anyway**

**How to verify the file is the *real* one** (recommended — protects against tampered copies floating around):
1. Right-click the downloaded `GimmeDat.exe` → **Properties** → **Details**. You should see:
   - **Product name:** GimmeDat
   - **Copyright:** Copyright (C) 2026 Kaiden. Licensed under GPL-3.0.
   - **Company:** Kaiden
   - **File version:** matches the release
2. Compare its **SHA256** to the one published on the Release page. In PowerShell:
   ```powershell
   Get-FileHash GimmeDat.exe -Algorithm SHA256
   ```
   The hash must match exactly. If it differs by even one character, **don't run it** — that copy was modified by someone else.

**Why no warning will eventually appear:** Microsoft SmartScreen builds reputation per-publisher per-binary over downloads. Once enough people have downloaded GimmeDat without flagging it, the warning will quietly stop showing up. (Code-signing speeds this up but doesn't skip it — only an *EV* cert removes the prompt instantly, and those run several hundred dollars per year.)

**The source is right here on GitHub.** Anyone can read every line — that's the whole point of open source. If you're security-conscious, build the exe yourself with `BUILD.md`; the hash will match what's published in the release.

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
