from fractions import Fraction
from pathlib import Path
import subprocess
import sys
from typing import Any

import addon_utils
import bpy


ADDON_DEPS = ['rk_importer']

def get_full_addon_id(addon: str) -> str | None:
    for module in addon_utils.modules(): # type: ignore
        if module.__name__.split('.')[-1] == addon:
            return module.__name__

def check_addon(addon: str) -> bool:
    full_id = get_full_addon_id(addon)
    if not full_id:
        print(f'Cannot find {addon}')
        return False
    addon_utils.enable(full_id)
    return addon_utils.check(full_id)[1]

def enable_addon_deps():
    """
    Check if all the addon dependencies exist. Returns a list of all unavailable dependencies.

    Returns:
        list[str]: List of unavailable required addons.
    """
    
    failed: list[str] = []
    for addon in ADDON_DEPS:
        if not check_addon(addon):
            failed.append(addon)
    
    return failed

def open_file(filepath: str | Path):
    image_viewer = {'linux':'xdg-open',
                    'win32':'explorer',
                    'darwin':'open'}[sys.platform]
    subprocess.Popen([image_viewer, filepath])


def blender_fps(target: float) -> tuple[int, float]:
    """
    Convert fps to blender fps/base_fps

    Args:
        target (float): Input fps

    Returns:
        tuple[int, float]: (fps, base_fps)
    """

    # NTSC-style rates (23.976, 29.97, 59.94, ...) are N / 1.001
    n = round(target * 1.001)
    if abs(n / 1.001 - target) < 0.001:
        return n, 1.001

    # Everything else: convert to a simple fraction.
    # str() avoids float noise (59.5 -> "59.5", not 59.5000000001)
    frac = Fraction(str(target)).limit_denominator(1000)
    return frac.numerator, float(frac.denominator)


