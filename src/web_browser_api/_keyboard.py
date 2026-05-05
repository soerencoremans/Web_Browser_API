import subprocess


def _xkb_query():
    """Return current X keyboard settings as a dict (layout/variant/options/model/rules)."""
    out = subprocess.check_output(["setxkbmap", "-query"], text=True)
    state = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            state[k.strip()] = v.strip()
    # Normalize keys we care about
    return {
        "layout": state.get("layout", ""),
        "variant": state.get("variant", ""),
        "options": state.get("options", ""),
        "model": state.get("model", ""),
        "rules": state.get("rules", ""),
    }


def _xkb_apply(state):
    """Apply a previously captured XKB state."""
    args = ["setxkbmap"]
    if state.get("rules"):
        args += ["-rules", state["rules"]]
    if state.get("model"):
        args += ["-model", state["model"]]
    if state.get("layout"):
        args += ["-layout", state["layout"]]
    if state.get("variant"):
        args += ["-variant", state["variant"]]
    # Reset options first to avoid accumulation, then set them if present
    args_reset = ["setxkbmap", "-option"]
    subprocess.run(args_reset, check=True)
    if state.get("options"):
        args += ["-option", state["options"]]
    subprocess.run(args, check=True)


def _switch_to_us():
    """Switch keyboard to US layout."""
    # Clear options then set us to avoid inherited weirdness
    subprocess.run(["setxkbmap", "-option"], check=True)
    subprocess.run(["setxkbmap", "us"], check=True)
