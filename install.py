
from pathlib import Path
import subprocess
import shutil
import tempfile
import sys

PATCH_DIR = Path(__file__).resolve().parent
GAME_DIR = PATCH_DIR.parent / "A Game of Thrones The Board Game"
XDELTA = Path(r"C:\Tools\xdelta3\xdelta3.exe")
BACKUP_DIR = GAME_DIR / "RussianLocalization_Backup"

PATCHES = [
    "AGameOfThronesTheBoardGame_Data/Managed/core-localization.dll",
    "AGameOfThronesTheBoardGame_Data/Managed/iron-client.dll",
    "AGameOfThronesTheBoardGame_Data/level2",
    "AGameOfThronesTheBoardGame_Data/level4",
    "AGameOfThronesTheBoardGame_Data/resources.assets",
]

NEW_FILES = [
    "AGameOfThronesTheBoardGame_Data/StreamingAssets/Localization/ru_RU.txt",
]


def install():
    print("A Game of Thrones - Russian Localization")
    print("---------------------------------------")

    if not GAME_DIR.is_dir():
        raise RuntimeError("Game folder not found")

    if not XDELTA.is_file():
        raise RuntimeError("xdelta3.exe not found")

    if BACKUP_DIR.exists():
        raise RuntimeError(
            "Backup already exists. Restore the original game first."
        )

    # Check all required files before changing anything
    for name in PATCHES:
        if not (GAME_DIR / name).is_file():
            raise RuntimeError(f"Game file missing: {name}")
        if not (PATCH_DIR / (name + ".xdelta")).is_file():
            raise RuntimeError(f"Patch missing: {name}")

    for name in NEW_FILES:
        if not (PATCH_DIR / name).is_file():
            raise RuntimeError(f"Localization file missing: {name}")
        if (GAME_DIR / name).exists():
            raise RuntimeError(
                f"File already exists: {name}. Restore the clean game."
            )

    # Decode patches into temporary files first
    with tempfile.TemporaryDirectory() as temp:
        staged = Path(temp)

        for name in PATCHES:
            source = GAME_DIR / name
            patch = PATCH_DIR / (name + ".xdelta")
            output = staged / name
            output.parent.mkdir(parents=True, exist_ok=True)

            print(f"Verifying: {name}")

            subprocess.run(
                [
                    str(XDELTA), "-d", "-f",
                    "-s", str(source),
                    str(patch), str(output)
                ],
                check=True
            )

        # Back up originals
        BACKUP_DIR.mkdir()

        for name in PATCHES:
            backup = BACKUP_DIR / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(GAME_DIR / name, backup)

        # Install with rollback on failure
        try:
            for name in PATCHES:
                shutil.copy2(staged / name, GAME_DIR / name)
                print(f"Installed: {name}")

            for name in NEW_FILES:
                destination = GAME_DIR / name
                destination.parent.mkdir(
                    parents=True, exist_ok=True
                )
                shutil.copy2(PATCH_DIR / name, destination)
                print(f"Installed: {name}")

        except Exception:
            print("Installation failed. Restoring backups...")

            for name in PATCHES:
                shutil.copy2(BACKUP_DIR / name, GAME_DIR / name)

            for name in NEW_FILES:
                (GAME_DIR / name).unlink(missing_ok=True)

            shutil.rmtree(BACKUP_DIR)
            raise

    print()
    print("SUCCESS! Russian localization installed.")
    print(f"Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    try:
        install()
    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)
