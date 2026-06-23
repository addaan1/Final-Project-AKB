from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
DVC_CONFIG_LOCAL = ROOT / ".dvc" / "config.local"
PYDRIVE2_CACHE_ROOT = (
    Path.home()
    / "AppData"
    / "Local"
    / "Packages"
    / "PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0"
    / "LocalCache"
    / "Local"
    / "pydrive2fs"
    / "Cache"
)


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def run_dvc(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "dvc", *args],
        cwd=ROOT,
        check=True,
    )


def reset_auth_cache(client_id: str) -> None:
    cache_dir = PYDRIVE2_CACHE_ROOT / client_id
    token_file = cache_dir / "default.json"
    if not token_file.exists():
        print("No existing Google Drive token cache was found.")
        return

    backup = cache_dir / "default.reset-backup.json"
    if backup.exists():
        backup.unlink()
    token_file.replace(backup)
    print(f"Moved cached Google Drive token to: {backup}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset-auth",
        action="store_true",
        help="Remove the saved Google Drive OAuth token so DVC asks to log in again.",
    )
    args = parser.parse_args()

    if not ENV_PATH.exists():
        print("Missing .env. Copy .env.example to .env and fill the Google Drive values first.")
        return 1

    env_values = read_env(ENV_PATH)
    client_id = env_values.get("GDRIVE_CLIENT_ID", "")
    client_secret = env_values.get("GDRIVE_CLIENT_SECRET", "")

    missing = [
        key
        for key, value in {
            "GDRIVE_CLIENT_ID": client_id,
            "GDRIVE_CLIENT_SECRET": client_secret,
        }.items()
        if not value
    ]
    if missing:
        print(f"Missing required keys in .env: {', '.join(missing)}")
        return 1

    run_dvc("remote", "modify", "--local", "gdrive_remote", "gdrive_client_id", client_id)
    run_dvc(
        "remote",
        "modify",
        "--local",
        "gdrive_remote",
        "gdrive_client_secret",
        client_secret,
    )
    if args.reset_auth:
        reset_auth_cache(client_id)

    print("Saved Google Drive OAuth client settings to .dvc/config.local")
    print(f"Local config file: {DVC_CONFIG_LOCAL}")
    print("Next steps:")
    print("  1. Make sure the Google account you will choose has access to the Drive folder.")
    print("  2. Run `dvc pull` or `dvc push` from the activated virtualenv.")
    print("  3. Approve the browser consent screen on the first run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
