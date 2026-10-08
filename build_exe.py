"""Build standalone executables with PyInstaller."""

import subprocess
import sys
from pathlib import Path


def build_gui():
    """Build the GUI executable."""
    print("Building GUI executable...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "SC2ReplayParser",
        "--icon", str(Path(__file__).parent / "sc2_frog_icon.ico"),
        "--distpath", str(Path(__file__).parent / "dist"),
        "--workpath", str(Path(__file__).parent / "build"),
        "--specpath", str(Path(__file__).parent),
        "--paths", str(Path(__file__).parent),
        "--hidden-import", "sc2reader",
        "--hidden-import", "PyQt6",
        "--collect-data", "sc2reader",
        str(Path(__file__).parent / "sc2_replay_parser" / "gui.py")
    ]
    subprocess.run(cmd, check=True)
    print(f"Built GUI: {Path(__file__).parent / 'dist' / 'SC2ReplayParser.exe'}")


def build_organizer():
    """Build the organizer CLI executable."""
    print("Building organizer CLI executable...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile",
        "--name", "replay_organizer",
        "--distpath", str(Path(__file__).parent / "dist"),
        "--workpath", str(Path(__file__).parent / "build"),
        "--specpath", str(Path(__file__).parent),
        "--paths", str(Path(__file__).parent),
        "--hidden-import", "sc2reader",
        "--collect-data", "sc2reader",
        str(Path(__file__).parent / "sc2_replay_parser" / "organizer.py")
    ]
    subprocess.run(cmd, check=True)
    print(f"Built organizer: {Path(__file__).parent / 'dist' / 'replay_organizer.exe'}")


def build_parser():
    """Build the parser CLI executable."""
    print("Building parser CLI executable...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile",
        "--name", "sc2_replay_parser",
        "--distpath", str(Path(__file__).parent / "dist"),
        "--workpath", str(Path(__file__).parent / "build"),
        "--specpath", str(Path(__file__).parent),
        "--paths", str(Path(__file__).parent),
        "--hidden-import", "sc2reader",
        "--collect-data", "sc2reader",
        str(Path(__file__).parent / "sc2_replay_parser" / "parser.py")
    ]
    subprocess.run(cmd, check=True)
    print(f"Built parser: {Path(__file__).parent / 'dist' / 'sc2_replay_parser.exe'}")


def main():
    """Build all executables."""
    print("Building SC2 Replay Organizer executables...")
    build_gui()
    build_organizer()
    build_parser()
    print("\nAll executables built successfully in dist/")


if __name__ == "__main__":
    main()
