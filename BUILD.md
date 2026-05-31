# Building GimmeDat (Windows)

## 1. Install Python 3.11+
<https://www.python.org/downloads/> — check **"Add Python to PATH"**.

## 2. Install dependencies
```bash
pip install -r requirements.txt
```
(See `requirements.txt` for the full list — `customtkinter pillow imageio-ffmpeg tkinterdnd2 pyinstaller` + video-extraction backend.)

## 3. Run from source (optional)
```bash
python GimmeDat_source.py
```

## 4. Build the single-file .exe
Run from the project root (where `GimmeDat_source.py` is):

```bash
pyinstaller --onefile --noconsole --name GimmeDat ^
  --icon="logos\GimmeDat_icon.ico" ^
  --add-data="logos;logos" ^
  --add-data="assets;assets" ^
  --collect-all imageio_ffmpeg ^
  --collect-all tkinterdnd2 ^
  GimmeDat_source.py
```

(`^` are CMD line-continuations — or paste it all on one line.)

### What each flag does
| Flag | Purpose |
|------|---------|
| `--onefile` | one portable `.exe` |
| `--noconsole` | no black terminal window |
| `--icon` | taskbar / file icon |
| `--add-data="logos;logos"` | bundles the window icon |
| `--add-data="assets;assets"` | bundles the background-music mp3 |
| `--collect-all imageio_ffmpeg` | bundles ffmpeg (HD merge + MP3) |
| `--collect-all tkinterdnd2` | bundles drag-and-drop support |

## 5. Result
`dist\GimmeDat.exe` — double-click, no install needed.

## Optional assets (auto-detected if present in `assets/`)
| File | Effect |
|------|--------|
| `assets\bgm.mp3` | background music (already included) |
| `assets\mascot_idle/excited/happy/sad.png` | real mascot art (140×140) instead of the pixel cat |
| `assets\platform_<key>.png` | custom platform icon (22×22) instead of the drawn glyph |

## Notes
- **Close GimmeDat.exe before rebuilding**, or you'll get *"Access is denied"*.
- Video sites change often. If one breaks: `pip install -U -r requirements.txt`, then rebuild.
- Build from a **non-admin** terminal (PyInstaller warns otherwise).
- The harmless `Library not found: ...DLL` warnings during build are standard Windows system DLLs — ignore them.
