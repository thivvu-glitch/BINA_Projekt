from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


PYTHON_VERSION = "3.11"
UV_LINK_MODE = "copy"


def run_command(command: list[str], cwd: Path) -> None:
    print(f"[run] {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    project_root = Path(__file__).resolve().parent
    pyproject_file = project_root / "pyproject.toml"

    if not pyproject_file.exists():
        print(f"Missing project file: {pyproject_file}")
        return 1

    if shutil.which("uv") is None:
        print("uv is not installed or not available in PATH.")
        print("Install uv: https://docs.astral.sh/uv/getting-started/installation/")
        return 1

    try:
        # Ensure the requested Python version is available to uv.
        run_command(["uv", "python", "install", PYTHON_VERSION], cwd=project_root)

        print(f"Syncing environment from: {pyproject_file}")
        run_command(
            [
                "uv",
                "sync",
                "--link-mode",
                UV_LINK_MODE,
            ],
            cwd=project_root,
        )
    except subprocess.CalledProcessError as error:
        print(f"Command failed with exit code {error.returncode}.")
        return error.returncode

    print("\nSetup complete.")
    if os.name == "nt":
        print(r"Activate env (PowerShell): .\.venv\Scripts\Activate.ps1")
    else:
        print("Activate env: source .venv/bin/activate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())