# Browser Profiles

Named Chrome profiles are stored here.

Each profile uses this layout:

```text
profiles/
  profile_x/
    profile_x_file/
    profile_x_cookies.txt
```

- `profile_x_file/` is Chrome's user-data directory for that profile.
- `profile_x_cookies.txt` lists the sites/domains whose cookies were intentionally prepared in the profile.

Do not run automation directly against a golden profile if you need it to remain unchanged. Copy it to a working profile first, run against the copy, then discard the copy.
