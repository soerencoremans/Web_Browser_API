# src/web_browser_api/__init__.py
# Lightweight package init to keep imports side-effect free and fast.
# Heavy dependencies (e.g., undetected-chromedriver, pyautogui) are imported lazily.

__version__ = "0.1.0"

# Public API surface
__all__ = [
    "get_driver", "close_driver", "nuke_chrome_profile",
    "get_profile_paths", "ensure_profile", "add_cookie_sites", "read_cookie_sites",
    "list_profiles", "delete_profile",
    "switch_to_latest_tab", "open_new_tab", "close_current_tab", "focus_chrome_window",
    "generate_password", "generate_bot_identity",
    "type_like_human", "human_pause", "move_mouse",
    "get_element_center", "get_element_click_point", "click_element",
    "click_and_hold_element", "click_and_hold_pos", "extract_text_from_chrome_window",
    # debug helpers
    "get_current_tab_url", "get_page_source",
]

# Lazy attribute access (PEP 562): import submodules only when a symbol is first used.
_def_to_module = {
    # driver
    "get_driver": ".driver",
    "close_driver": ".driver",
    "nuke_chrome_profile": ".driver",
    # profiles
    "get_profile_paths": ".profiles",
    "ensure_profile": ".profiles",
    "add_cookie_sites": ".profiles",
    "read_cookie_sites": ".profiles",
    "list_profiles": ".profiles",
    "delete_profile": ".profiles",
    # api
    "switch_to_latest_tab": ".api",
    "open_new_tab": ".api",
    "close_current_tab": ".api",
    "focus_chrome_window": ".api",
    "generate_password": ".api",
    "generate_bot_identity": ".api",
    "type_like_human": ".api",
    "human_pause": ".api",
    "move_mouse": ".api",
    "get_element_center": ".api",
    "get_element_click_point": ".api",
    "click_element": ".api",
    "click_and_hold_element": ".api",
    "click_and_hold_pos": ".api",
    "extract_text_from_chrome_window": ".api",
    # debug
    "get_current_tab_url": ".debug_functions",
    "get_page_source": ".debug_functions",
}

def __getattr__(name):
    import importlib
    module_rel = _def_to_module.get(name)
    if module_rel is None:
        raise AttributeError(f"module 'web_browser_api' has no attribute {name!r}")
    mod = importlib.import_module(module_rel, __name__)
    attr = getattr(mod, name)
    globals()[name] = attr  # cache for future lookups
    return attr
