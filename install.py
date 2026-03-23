from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PYTHON_VERSION = "3.11"
UV_LINK_MODE = "copy"


def run_command(command: list[str], cwd: Path) -> None:
    print(f"[run] {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def get_venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main() -> int:
    project_root = Path(__file__).resolve().parent
    requirements_file = project_root / "requirements.txt"
    venv_dir = project_root / ".venv"

    if not requirements_file.exists():
        print(f"Missing requirements file: {requirements_file}")
        return 1

    if shutil.which("uv") is None:
        print("uv is not installed or not available in PATH.")
        print("Install uv: https://docs.astral.sh/uv/getting-started/installation/")
        return 1

    try:
        # Ensure the requested Python version is available to uv.
        run_command(["uv", "python", "install", PYTHON_VERSION], cwd=project_root)

        venv_python = get_venv_python(venv_dir)
        if not venv_python.exists():
            # On Windows, .venv can be a reparse point; check for interpreter instead of folder.
            run_command(["uv", "venv", "--python", PYTHON_VERSION, str(venv_dir)], cwd=project_root)
            if not venv_python.exists():
                print(f"Virtual environment Python not found: {venv_python}")
                return 1
        run_command(
            [
                "uv",
                "pip",
                "install",
                "--link-mode",
                UV_LINK_MODE,
                "--python",
                str(venv_python),
                "-r",
                str(requirements_file),
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