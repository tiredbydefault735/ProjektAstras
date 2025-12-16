"""
Build script for ProjektAstras using PyInstaller.
Easier alternative to Nuitka - no C compiler required!
"""

import subprocess
import sys
from pathlib import Path

def build():
    """Build the application with PyInstaller."""
    
    # Project root
    project_root = Path(__file__).parent
    
    # Main entry point
    main_file = project_root / "frontend" / "main.py"
    
    # Output name
    output_name = "ProjektAstras"
    
    # Build command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",  # Single EXE file
        "--windowed",  # No console window (GUI app)
        "--name", output_name,  # Output name
        # Add data files (static folder)
        "--add-data", f"{project_root / 'static'};static",
        # Add backend module
        "--hidden-import", "backend",
        "--hidden-import", "backend.model",
        # Add frontend modules
        "--hidden-import", "frontend.screens.start_screen",
        "--hidden-import", "frontend.screens.simulation_screen",
        "--hidden-import", "frontend.screens.simulation_map",
        "--hidden-import", "frontend.screens.settings_screen",
        "--hidden-import", "frontend.styles.stylesheet",
        "--hidden-import", "frontend.styles.color_presets",
        # Add utils
        "--hidden-import", "utils",
        # Working directory
        f"--workpath={project_root / 'build' / 'work'}",
        f"--distpath={project_root / 'dist'}",
        f"--specpath={project_root / 'build'}",
        str(main_file)
    ]
    
    print("Building ProjektAstras with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    # Run the build
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*80)
        print("Build successful!")
        print(f"Executable location: {project_root / 'dist' / f'{output_name}.exe'}")
        print("="*80)
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code {e.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
