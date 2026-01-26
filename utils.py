"""
Utility functions for resource path handling.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Union


def get_static_path(relative_path: Union[str, Path]) -> Path:
    """
    Get the absolute path to a static resource file.
    Works both in development and when frozen with PyInstaller.

    Args:
        relative_path: Path relative to the static/ directory

    Returns:
        Path object to the resource
    """
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS) / "static"
    else:
        # Running in development
        base_path = Path(__file__).parent / "static"

    return base_path / relative_path
