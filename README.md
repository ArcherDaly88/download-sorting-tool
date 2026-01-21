# Download Sorting Tool

A lightweight, event-driven utility for Windows that automatically routes downloaded files out of the Downloads folder into appropriate destinations (Pictures, Videos, Music, Documents, etc.).

# Download Sorting Tool

Designed to keep the Downloads folder empty by default by automatically routing downloaded files into appropriate user folders.

&

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

- Tested on Python 3.12 (Windows). Other versions are untested.


## Install dependency:

```bash
pip install watchdog

## Usage:

Run manually for testing:

python download_sorter.py


The script uses Path.home() and therefore automatically targets the currently logged-in user's folders.

Running silently at startup

Recommended method: Windows Task Scheduler

Program/script:

pythonw.exe


Arguments:

"C:\Path\To\download_sorter.py"


Start in:

C:\Path\To\


Trigger: At log on (Any user)

Using pythonw.exe prevents any console window from appearing.

Notes on OneDrive

If your Pictures folder is redirected by OneDrive, update the PICTURES path in the script accordingly:

PICTURES = Path.home() / "OneDrive" / "Pictures"


Videos and Music are typically not redirected.

## Design Notes

- No GUI by design.
- No external config files unless there is a clear demand.
- Sorting rules are defined directly in code for transparency and simplicity.
