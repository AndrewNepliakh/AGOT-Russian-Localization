
from pathlib import Path
import subprocess
import tempfile
import shutil

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parent / "AGOT-Russian-Localization"
BASE = "11143c7"
XDELTA = Path(r"C:\Tools\xdelta3\xdelta3.exe")


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT
    )


def main():
    if not XDELTA.is_file():
        raise SystemExit("ERROR: xdelta3.exe not found")

    # Check tracked files for uncommitted changes
    result = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--"],
        cwd=ROOT
    )

    if result.returncode != 0:
        raise SystemExit("ERROR: Commit your changes first")

    # Find files changed since the original game
    files = git(
        "diff",
        "--name-only",
        "--diff-filter=ACMRT",
        "-z",
        BASE,
        "HEAD"
    ).decode("utf-8").split("\0")

    files = [name for name in files if name]

    if not files:
        print("No modified files found")
        return

    OUTPUT.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(files)} modified files")

    with tempfile.TemporaryDirectory() as temp:
        original_path = Path(temp) / "original.bin"

        for name in files:
            current = ROOT / name

            if not current.is_file():
                print(f"SKIPPED: {name}")
                continue

            target = OUTPUT / (name + ".xdelta")
            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Get original file from first commit
            result = subprocess.run(
                ["git", "show", f"{BASE}:{name}"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            if result.returncode != 0:
                # New localization file
                destination = OUTPUT / name
                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                shutil.copy2(current, destination)
                print(f"NEW: {name}")
                continue

            original_path.write_bytes(result.stdout)

            # Generate binary patch
            subprocess.run(
                [
                    str(XDELTA),
                    "-e",
                    "-f",
                    "-s",
                    str(original_path),
                    str(current),
                    str(target)
                ],
                check=True
            )

            print(f"PATCH: {name}")

    print()
    print("SUCCESS!")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
