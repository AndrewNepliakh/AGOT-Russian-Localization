from pathlib import Path, PurePosixPath
import json
import shutil
import subprocess
import sys
import tempfile

PATCH_DIR = Path(__file__).resolve().parent
GAME_DIR = PATCH_DIR.parent / "A Game of Thrones The Board Game"
BACKUP_DIR = GAME_DIR / "RussianLocalization_Backup"
MANIFEST = PATCH_DIR / "generated_files.json"
XDELTA = Path(r"C:\Tools\xdelta3\xdelta3.exe")
DATA_PREFIX = "AGameOfThronesTheBoardGame_Data/"


def read_manifest():
    if not MANIFEST.is_file():
        raise RuntimeError("generated_files.json not found")
    entries = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("Manifest must be a non-empty JSON list")

    patches, new_files = [], []
    seen = set()
    for entry in entries:
        if not isinstance(entry, str):
            raise RuntimeError("Invalid manifest entry")
        path = PurePosixPath(entry)
        if (not entry.startswith(DATA_PREFIX) or "\\" in entry
                or path.is_absolute() or any(part in (".", "..") for part in entry.split("/"))
                or any(not part for part in entry.split("/"))):
            raise RuntimeError(f"Unsafe manifest path: {entry}")
        is_patch = entry.endswith(".xdelta")
        target = entry[:-7] if is_patch else entry
        if not target or target in seen:
            raise RuntimeError(f"Duplicate or invalid target: {entry}")
        seen.add(target)
        if not (PATCH_DIR / entry).is_file():
            raise RuntimeError(f"Missing payload: {entry}")
        (patches if is_patch else new_files).append((entry, target))
    return patches, new_files


def install():
    print("A Game of Thrones - Russian Localization")
    print("---------------------------------------")
    if not GAME_DIR.is_dir():
        raise RuntimeError(f"Game folder not found: {GAME_DIR}")
    patches, new_files = read_manifest()
    if patches and not XDELTA.is_file():
        raise RuntimeError(f"xdelta3.exe not found: {XDELTA}")
    if BACKUP_DIR.exists():
        raise RuntimeError("Backup already exists. Restore the original game first.")

    for _, target in patches:
        if not (GAME_DIR / target).is_file():
            raise RuntimeError(f"Original game file missing: {target}")
    for _, target in new_files:
        if (GAME_DIR / target).exists():
            raise RuntimeError(f"File already exists: {target}. Restore the clean game.")

    with tempfile.TemporaryDirectory() as temp:
        staged = Path(temp) / "staged"
        backup_stage = Path(temp) / "backup"
        # Decode and verify all patches before changing the game.
        for entry, target in patches:
            output = staged / target
            output.parent.mkdir(parents=True, exist_ok=True)
            print(f"Verifying: {target}")
            subprocess.run(
                [str(XDELTA), "-d", "-f", "-s", str(GAME_DIR / target),
                 str(PATCH_DIR / entry), str(output)],
                check=True,
            )
        # Stage all new files and backups before modifying anything.
        for entry, target in new_files:
            output = staged / target
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PATCH_DIR / entry, output)
        for _, target in patches:
            backup = backup_stage / target
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(GAME_DIR / target, backup)

        installed_new = []
        replaced = []
        try:
            # Keep the backup inside the game directory for later restoration.
            shutil.copytree(backup_stage, BACKUP_DIR)
            for _, target in patches:
                replaced.append(target)
                shutil.copy2(staged / target, GAME_DIR / target)
                print(f"Installed patch: {target}")
            for _, target in new_files:
                destination = GAME_DIR / target
                destination.parent.mkdir(parents=True, exist_ok=True)
                installed_new.append(target)
                shutil.copy2(staged / target, destination)
                print(f"Installed new file: {target}")
            # Record added files for a future uninstaller.
            (BACKUP_DIR / "added_files.json").write_text(
                json.dumps([target for _, target in new_files], indent=2),
                encoding="utf-8",
            )
        except Exception:
            print("Installation failed. Restoring originals...")
            for target in reversed(installed_new):
                (GAME_DIR / target).unlink(missing_ok=True)
            restore_errors = []
            for target in reversed(replaced):
                try:
                    shutil.copy2(backup_stage / target, GAME_DIR / target)
                except Exception as exc:
                    restore_errors.append(f"{target}: {exc}")
            if restore_errors:
                raise RuntimeError("Rollback incomplete! Backups retained in "
                                   f"{BACKUP_DIR}. Errors: {restore_errors}")
            if BACKUP_DIR.exists():
                shutil.rmtree(BACKUP_DIR)
            raise

    print("\nSUCCESS! Russian localization installed.")
    print(f"Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    try:
        install()
    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)
