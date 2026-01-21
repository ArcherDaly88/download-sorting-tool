# download-sorting-tool
# Download Sorting Tool

A lightweight, event-driven utility for Windows that automatically routes downloaded files out of the Downloads folder into appropriate destinations (Pictures, Videos, Music, Documents, etc.).

Designed to work correctly with modern browsers and OneDrive-redirected folders.

## What it does

- Watches the user's Downloads folder using filesystem events (no polling)
- Detects *real browser downloads* by tracking temporary download artifacts
- Moves completed downloads immediately to the correct destination
- Leaves manually copied or created files in Downloads untouched
- Works with OneDrive-redirected Pictures folders
- Can run silently at startup via Task Scheduler

## Routing rules (default)

- `.jpg .png .jpeg .webp` → Pictures
- `.mp4` → Videos
- `.mp3 .wav .m4a` → Music
- `.pdf` → Documents
- `.zip .7z .rar` → Downloads\\_Archives

Unmatched or manually placed files remain in Downloads.

## Requirements

- Windows 10 / 11
- Python 3.12+
- Python package: `watchdog`

Install dependency:

```bash
pip install watchdog

