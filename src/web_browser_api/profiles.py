from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROFILES_ROOT = Path("profiles")
_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class ProfilePaths:
    name: str
    container_dir: Path
    user_data_dir: Path
    cookies_manifest: Path


def _validate_profile_name(profile_name: str) -> str:
    if not profile_name:
        raise ValueError("profile_name must not be empty.")
    if not _PROFILE_NAME_RE.fullmatch(profile_name):
        raise ValueError("profile_name may only contain letters, numbers, underscores, and hyphens.")
    return profile_name


def get_profile_paths(profile_name: str, profiles_root: str | Path | None = None) -> ProfilePaths:
    """
    Return the filesystem paths for a named browser profile.

    Layout:
        profiles/<profile_name>/<profile_name>_file/
        profiles/<profile_name>/<profile_name>_cookies.txt
    """
    profile_name = _validate_profile_name(profile_name)
    root = Path(profiles_root or DEFAULT_PROFILES_ROOT).expanduser().resolve()
    container_dir = root / profile_name

    return ProfilePaths(
        name=profile_name,
        container_dir=container_dir,
        user_data_dir=container_dir / f"{profile_name}_file",
        cookies_manifest=container_dir / f"{profile_name}_cookies.txt",
    )


def ensure_profile(
    profile_name: str,
    profiles_root: str | Path | None = None,
    cookie_sites: list[str] | tuple[str, ...] | None = None,
) -> ProfilePaths:
    """
    Create the profile container, Chrome user-data directory, and cookie manifest.
    """
    paths = get_profile_paths(profile_name, profiles_root)
    paths.user_data_dir.mkdir(parents=True, exist_ok=True)

    if not paths.cookies_manifest.exists():
        paths.cookies_manifest.write_text("", encoding="utf-8")

    if cookie_sites:
        add_cookie_sites(profile_name, cookie_sites, profiles_root=profiles_root)

    return paths


def add_cookie_sites(
    profile_name: str,
    sites: list[str] | tuple[str, ...],
    profiles_root: str | Path | None = None,
) -> ProfilePaths:
    """
    Add site names/domains to the profile cookie manifest, preserving existing entries.
    """
    paths = ensure_profile(profile_name, profiles_root=profiles_root)

    existing = {
        line.strip()
        for line in paths.cookies_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    updated = sorted(existing | {site.strip() for site in sites if site.strip()})
    paths.cookies_manifest.write_text("\n".join(updated) + ("\n" if updated else ""), encoding="utf-8")
    return paths


def read_cookie_sites(profile_name: str, profiles_root: str | Path | None = None) -> list[str]:
    """
    Read the recorded cookie-source sites for a profile.
    """
    paths = get_profile_paths(profile_name, profiles_root)
    if not paths.cookies_manifest.exists():
        return []

    return [
        line.strip()
        for line in paths.cookies_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def list_profiles(profiles_root: str | Path | None = None) -> list[str]:
    """
    List profile names under the profiles root.
    """
    root = Path(profiles_root or DEFAULT_PROFILES_ROOT).expanduser().resolve()
    if not root.exists():
        return []

    return sorted(path.name for path in root.iterdir() if path.is_dir())


def delete_profile(profile_name: str, profiles_root: str | Path | None = None) -> None:
    """
    Remove an entire named profile container.
    """
    paths = get_profile_paths(profile_name, profiles_root)
    if paths.container_dir.exists():
        shutil.rmtree(paths.container_dir)
