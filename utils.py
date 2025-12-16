"""
Utility functions for ProjektAstras.
"""

import sys
from pathlib import Path


def get_resource_path(relative_path=None):
    """
    Get the absolute path to a resource, working in development and when frozen with PyInstaller.
    
    For PyInstaller onefile builds, resources are extracted to a temporary directory.
    
    Args:
        relative_path: Optional relative path to append (e.g., "static/fonts/Minecraft.ttf")
    
    Returns:
        Path object pointing to the resource location
    """
    # Check if running as frozen executable (PyInstaller sets sys._MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile: resources are in temporary extraction directory
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development mode
        # Go up from utils.py to project root
        base_path = Path(__file__).parent
    
    if relative_path:
        return base_path / relative_path
    return base_path


def get_static_path(relative_path=None):
    """
    Get path to static resources.
    
    Args:
        relative_path: Path relative to static/ (e.g., "fonts/Minecraft.ttf")
    
    Returns:
        Path object pointing to the static resource
    """
    if relative_path:
        return get_resource_path(f"static/{relative_path}")
    return get_resource_path("static")
