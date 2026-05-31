# Build GimmeDat

Windows · Python 3.11+

```bash
pip install -r requirements.txt
python GimmeDat_source.py          # run from source
```

Build the `.exe`:

```bash
pyinstaller --onefile --noconsole --name GimmeDat ^
  --icon="logos\GimmeDat_icon.ico" ^
  --version-file="version_info.txt" ^
  --add-data="logos;logos" ^
  --add-data="assets;assets" ^
  --collect-all imageio_ffmpeg ^
  --collect-all tkinterdnd2 ^
  GimmeDat_source.py
```

Output → `dist\GimmeDat.exe`.

### Optional assets — drop in `assets/`

| File | Effect |
|------|--------|
| `bgm.mp3` | background music (bundled) |
| `mascot_idle/excited/happy/sad.png` | custom mascot art (140×140) |
| `platform_<key>.png` | custom platform icon (22×22) |

### Notes
- Close `GimmeDat.exe` before rebuilding.
- `Library not found: ...DLL` warnings during build are standard Windows system DLLs — harmless.
