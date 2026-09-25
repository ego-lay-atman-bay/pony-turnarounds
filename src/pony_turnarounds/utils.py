from typing import Any

import bpy
import addon_utils

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
