import os
import shutil
from pathlib import Path

import undetected_chromedriver as uc

from .profiles import ensure_profile, get_profile_paths

PROFILE_PATH = os.path.expanduser("~/selenium/chrome-profile")
DEFAULT_BROWSER_VERSION_MAIN = int(os.environ.get("WEB_BROWSER_API_BROWSER_VERSION_MAIN", "147"))
driver: uc.Chrome | None = None
_driver_profile_path: str | None = None


def nuke_chrome_profile(profile_name: str | None = None, profiles_root: str | Path | None = None):
    """
    Completely remove a Chrome user profile.
    """
    profile_path = (
        get_profile_paths(profile_name, profiles_root).user_data_dir
        if profile_name
        else Path(PROFILE_PATH).expanduser()
    )

    if profile_path.exists():
        shutil.rmtree(profile_path)
        print(f"Deleted Chrome profile at {profile_path}")
    else:
        print(f"No Chrome profile found at {profile_path}")


def get_driver(
    session_id=None,
    profile_name: str | None = None,
    reset_profile: bool | None = None,
    profiles_root: str | Path | None = None,
    cookie_sites: list[str] | tuple[str, ...] | None = None,
    browser_version_main: int | None = None,
):
    _ = session_id  # Reserved for backwards compatibility with older callers.
    global driver, _driver_profile_path

    if profile_name:
        paths = ensure_profile(profile_name, profiles_root=profiles_root, cookie_sites=cookie_sites)
        profile_path = paths.user_data_dir
        should_reset = False if reset_profile is None else reset_profile
    else:
        profile_path = Path(PROFILE_PATH).expanduser()
        should_reset = True if reset_profile is None else reset_profile

    requested_profile_path = str(profile_path.resolve())
    if driver is not None:
        if _driver_profile_path and _driver_profile_path != requested_profile_path:
            raise RuntimeError(
                "A Chrome driver is already running with a different profile. "
                "Call close_driver() before switching profiles."
            )
        return driver

    if driver is None:
        print("Launching undetected Chrome browser...")
        if should_reset:
            nuke_chrome_profile(profile_name=profile_name, profiles_root=profiles_root)
        profile_path.mkdir(parents=True, exist_ok=True)

        options = uc.ChromeOptions()
        options.user_data_dir = str(profile_path)
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--password-store=basic")
        options.add_argument("--lang=en-US")
        options.add_argument("--window-size=1280,720")
        options.add_argument("--start-maximized")

        version_main = browser_version_main or DEFAULT_BROWSER_VERSION_MAIN
        driver = uc.Chrome(options=options, headless=False, version_main=version_main)
        _driver_profile_path = requested_profile_path
        print("Undetected Chrome driver launched successfully.")
    return driver


def close_driver():
    global driver, _driver_profile_path
    if driver is not None:
        try:
            driver.quit()
        finally:
            driver = None
            _driver_profile_path = None
    else:
        print("No Chrome driver is currently running.")
