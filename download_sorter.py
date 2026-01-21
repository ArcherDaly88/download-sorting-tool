from pathlib import Path
import time
import shutil
import traceback

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Paths ---
DOWNLOADS = Path.home() / "Downloads"
VIDEOS = Path.home() / "Videos"
DOCUMENTS = Path.home() / "Documents"
PICTURES = Path.home() / "OneDrive" / "Pictures"
MUSIC  = Path.home() / "Music"
ARCHIVES = DOWNLOADS / "_Archives"

# --- Rules ---
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a"}
ARCHIVE_EXTS = {".zip", ".7z", ".rar"}

# Browser temp extensions (Chrome/Edge/Firefox variants)
TEMP_EXTS = {".crdownload", ".part", ".tmp"}

# --- Stability gating ---
POLL_INTERVAL = 0.5
STABLE_SECONDS = 2.0
MAX_WAIT_SECONDS = 180  # 3 minutes

# --- Download-only gating ---
# We only move a final file if we've seen a temp-download artifact shortly beforehand.
# This prevents manual copies/creates from being moved.
TEMP_SEEN_TTL_SECONDS = 600  # keep temp markers for 10 minutes


def now_s() -> float:
    return time.time()


def purge_old(markers: dict[str, float]) -> None:
    cutoff = now_s() - TEMP_SEEN_TTL_SECONDS
    old_keys = [k for k, ts in markers.items() if ts < cutoff]
    for k in old_keys:
        markers.pop(k, None)


def wait_until_stable(path: Path) -> bool:
    """Wait until file size stops changing for STABLE_SECONDS."""
    start = now_s()
    last_size = -1
    last_change = now_s()

    while True:
        if not path.exists():
            return False

        try:
            size = path.stat().st_size
        except OSError:
            return False

        t = now_s()

        if size != last_size:
            last_size = size
            last_change = t

        if (t - last_change) >= STABLE_SECONDS:
            return True

        if (t - start) >= MAX_WAIT_SECONDS:
            return False

        time.sleep(POLL_INTERVAL)


def unique_dest(dest_dir: Path, name: str) -> Path:
    """If filename exists, append (1), (2), etc."""
    target = dest_dir / name
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def route_destination(ext: str) -> Path | None:
    if ext == ".mp4":
        return VIDEOS
    if ext == ".pdf":
        return DOCUMENTS
    if ext in IMAGE_EXTS:
        return PICTURES
    if ext in AUDIO_EXTS:
        return MUSIC
    if ext in ARCHIVE_EXTS:
        return ARCHIVES
    return None


def maybe_move(path: Path, temp_markers: dict[str, float]):
    """
    Move eligible files out of Downloads after they are stable,
    but ONLY if we believe they came from an actual browser download.
    """
    try:
        if not path.exists() or not path.is_file():
            return

        ext = path.suffix.lower()

        # Never move temp download artifacts
        if ext in TEMP_EXTS:
            return

        dest_dir = route_destination(ext)
        if dest_dir is None:
            return  # not a type we manage

        # DOWNLOAD-ONLY CHECK:
        # Only proceed if we have seen a temp-download artifact recently.
        purge_old(temp_markers)
        key = path.name.lower()
        if key not in temp_markers:
            # Not marked as downloaded; treat as manual placement and leave it.
            print("SKIP (not marked as download):", path.name)
            return

        # Ensure the download is complete (size stable)
        if not wait_until_stable(path):
            print("SKIP (not stable):", path.name)
            return

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = unique_dest(dest_dir, path.name)

        shutil.move(str(path), str(dest))
        print("MOVED:", path.name, "->", dest)

        # marker no longer needed
        temp_markers.pop(key, None)

    except Exception as e:
        print("ERROR in maybe_move:", path, "-", e)
        traceback.print_exc()


class Handler(FileSystemEventHandler):
    """
    This handler implements "download-only routing".

    Logic:
    - If we see a temp artifact (e.g. *.crdownload), remember it.
    - When that temp artifact is renamed to a final filename, mark the final filename as downloaded.
    - Only files with that mark are eligible for moving.
    """

    def __init__(self):
        super().__init__()
        self.temp_markers: dict[str, float] = {}

    def on_created(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        ext = src.suffix.lower()

        # Track temp artifacts created by browsers
        if ext in TEMP_EXTS:
            self.temp_markers[src.name.lower()] = now_s()
            print("EVENT temp created:", event.src_path)
            return

        # Final-file creates (manual copy / manual create) are NOT moved.
        print("EVENT created:", event.src_path)
        # No maybe_move here by design.

    def on_moved(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        dst = Path(event.dest_path)

        print("EVENT moved:", event.src_path, "->", event.dest_path)

        src_ext = src.suffix.lower()
        dst_ext = dst.suffix.lower()

        # If a temp artifact is being renamed to a final file, mark final as downloaded
        if src_ext in TEMP_EXTS and dst_ext not in TEMP_EXTS:
            purge_old(self.temp_markers)
            # Mark the final filename as downloaded
            self.temp_markers[dst.name.lower()] = now_s()
            # Also remove the old temp marker
            self.temp_markers.pop(src.name.lower(), None)

            # Now we can attempt to move the final file (if it matches our routing rules)
            maybe_move(dst, self.temp_markers)
            return

        # If something else was renamed within Downloads, do nothing by default.


def main():
    print("DEBUG: scheduling observer on:", DOWNLOADS)

    obs = Observer()
    obs.schedule(Handler(), str(DOWNLOADS), recursive=False)
    obs.start()

    print("Watching:", DOWNLOADS)
    print("Download-only rules:")
    print("  .mp4 -> Videos | .pdf -> Documents | images -> Pictures | audio -> Music | archives -> Downloads\\_Archives")
    print("  Manual copies/creates in Downloads will NOT be moved.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    finally:
        obs.join()


if __name__ == "__main__":
    main()
