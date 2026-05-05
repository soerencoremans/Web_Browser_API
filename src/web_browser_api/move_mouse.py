import collections
import math
import platform
import random
import sys
import time
from functools import partial

import numpy as np
import pyautogui
import pyscreeze


MINIMUM_DURATION = 0.1
MINIMUM_SLEEP = 0.05

if sys.platform.startswith("java"):
    # from . import _pyautogui_java as platformModule
    raise NotImplementedError("Jython is not yet supported by PyAutoGUI.")
elif sys.platform == "darwin":
    from pyautogui import _pyautogui_osx as platformModule
elif sys.platform == "win32":
    from pyautogui import _pyautogui_win as platformModule
elif platform.system() == "Linux":
    from pyautogui import _pyautogui_x11 as platformModule
else:
    raise NotImplementedError(f"Your platform ({platform.system()}) is not supported by PyAutoGUI.")

if sys.version_info[0] == 2 or sys.version_info[0:2] in ((3, 1), (3, 2)):
    # Python 2 and 3.1 and 3.2 uses collections.Sequence
    from collections import Sequence
else:
    # Python 3.3+ uses collections.abc.Sequence
    from collections.abc import Sequence

def moveAlongPath(path, x=None, y=None, duration=0.0, tween=pyautogui.linear, _pause=True):
    """Moves the mouse cursor to a point on the screen.

    The x and y parameters detail where the mouse event happens. If None, the
    current mouse position is used. If a float value, it is rounded down. If
    outside the boundaries of the screen, the event happens at edge of the
    screen.

    Args:
      x (int, float, None, tuple, optional): The x position on the screen where the
        click happens. None by default. If tuple, this is used for x and y.
        If x is a str, it's considered a filename of an image to find on
        the screen with locateOnScreen() and click the center of.
      y (int, float, None, optional): The y position on the screen where the
        click happens. None by default.
      duration (float, optional): The amount of time it takes to move the mouse
        cursor to the xy coordinates. If 0, then the mouse cursor is moved
        instantaneously. 0.0 by default.
      tween (func, optional): The tweening function used if the duration is not
        0. A linear tween is used by default.

    Returns:
      None
    """
    x, y = _normalizeXYArgs(x, y)
    _mouseMoveDrag("move", x, y, 0, 0, duration, tween=tween, path=path)


def _mouseMoveDrag(moveOrDrag, x, y, xOffset, yOffset, duration, tween=pyautogui.linear, button=None, path=None):
    """Handles the actual move or drag event, since different platforms
    implement them differently.

    On Windows & Linux, a drag is a normal mouse move while a mouse button is
    held down. On OS X, a distinct "drag" event must be used instead.

    The code for moving and dragging the mouse is similar, so this function
    handles both. Users should call the moveTo() or dragTo() functions instead
    of calling _mouseMoveDrag().

    Args:
      moveOrDrag (str): Either 'move' or 'drag', for the type of action this is.
      x (int, float, None, optional): How far left (for negative values) or
        right (for positive values) to move the cursor. 0 by default.
      y (int, float, None, optional): How far up (for negative values) or
        down (for positive values) to move the cursor. 0 by default.
      xOffset (int, float, None, optional): How far left (for negative values) or
        right (for positive values) to move the cursor. 0 by default.
      yOffset (int, float, None, optional): How far up (for negative values) or
        down (for positive values) to move the cursor. 0 by default.
      duration (float, optional): The amount of time it takes to move the mouse
        cursor to the new xy coordinates. If 0, then the mouse cursor is moved
        instantaneously. 0.0 by default.
      tween (func, optional): The tweening function used if the duration is not
        0. A linear tween is used by default.
      button (str, int, optional): The mouse button released. TODO

    Returns:
      None
    """

    # The move and drag code is similar, but OS X requires a special drag event instead of just a move event when dragging.
    # See https://stackoverflow.com/a/2696107/1893164
    assert moveOrDrag in ("move", "drag"), f"moveOrDrag must be in ('move', 'drag'), not {moveOrDrag}"

    if sys.platform != "darwin":
        moveOrDrag = "move"  # Only OS X needs the drag event specifically.

    xOffset = int(xOffset) if xOffset is not None else 0
    yOffset = int(yOffset) if yOffset is not None else 0

    if x is None and y is None and xOffset == 0 and yOffset == 0:
        return  # Special case for no mouse movement at all.

    startx, starty = pyautogui.position()

    x = int(x) if x is not None else startx
    y = int(y) if y is not None else starty

    # x, y, xOffset, yOffset are now int.
    x += xOffset
    y += yOffset

    width, height = pyautogui.size()

    # Make sure x and y are within the screen bounds.
    # x = max(0, min(x, width - 1))
    # y = max(0, min(y, height - 1))

    # If the duration is small enough, just move the cursor there instantly.
    steps = [(x, y)]

    if duration > MINIMUM_DURATION:
        # Non-instant moving/dragging involves tweening:
        num_steps = max(width, height)
        sleep_amount = duration / num_steps
        if sleep_amount < MINIMUM_SLEEP:
            num_steps = int(duration / MINIMUM_SLEEP)
            sleep_amount = duration / num_steps

        steps = [path(tween(n / num_steps)) for n in range(num_steps + 1)]

    for tweenX, tweenY in steps:
        if len(steps) > 1:
            # A single step does not require tweening.
            time.sleep(sleep_amount)

        tweenX = int(round(tweenX))
        tweenY = int(round(tweenY))

        # Do a fail-safe check to see if the user moved the mouse to a fail-safe position, but not if the mouse cursor
        # moved there as a result of this function. (Just because tweenX and tweenY aren't in a fail-safe position
        # doesn't mean the user couldn't have moved the mouse cursor to a fail-safe position.)
        _conditionalFailSafe(tweenX, tweenY)

        if moveOrDrag == "move":
            platformModule._moveTo(tweenX, tweenY)
        elif moveOrDrag == "drag":
            platformModule._dragTo(tweenX, tweenY, button)
        else:
            raise NotImplementedError(f"Unknown value of moveOrDrag: {moveOrDrag}")

    _conditionalFailSafe(tweenX, tweenY)


def _conditionalFailSafe(x, y):
    if pyautogui.FAILSAFE and (x, y) in pyautogui.FAILSAFE_POINTS:
        pyautogui.failSafeCheck()


Point = collections.namedtuple("Point", "x y")


def _normalizeXYArgs(firstArg, secondArg):
    """
    Returns a ``Point`` object based on ``firstArg`` and ``secondArg``, which are the first two arguments passed to
    several PyAutoGUI functions. If ``firstArg`` and ``secondArg`` are both ``None``, returns the current mouse cursor
    position.

    ``firstArg`` and ``secondArg`` can be integers, a sequence of integers, or a string representing an image filename
    to find on the screen (and return the center coordinates of).
    """
    if firstArg is None and secondArg is None:
        return pyautogui.position()

    elif firstArg is None and secondArg is not None:
        return Point(int(pyautogui.position()[0]), int(secondArg))

    elif secondArg is None and firstArg is not None and not isinstance(firstArg, Sequence):
        return Point(int(firstArg), int(pyautogui.position()[1]))

    elif isinstance(firstArg, str):
        # If x is a string, we assume it's an image filename to locate on the screen:
        try:
            location = pyautogui.locateOnScreen(firstArg)
            # The following code only runs if pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION is not set to True, meaning that
            # locateOnScreen() returns None if the image can't be found.
            if location is not None:
                return pyautogui.center(location)
            else:
                return None
        except pyscreeze.ImageNotFoundException:
            raise pyscreeze.ImageNotFoundException

    elif isinstance(firstArg, Sequence):
        if len(firstArg) == 2:
            # firstArg is a two-integer tuple: (x, y)
            if secondArg is None:
                return Point(int(firstArg[0]), int(firstArg[1]))
            else:
                raise pyautogui.PyAutoGUIException(
                    f"When passing a sequence for firstArg, secondArg must not be passed (received {secondArg!r})."
                )
        elif len(firstArg) == 4:
            # firstArg is a four-integer tuple, (left, top, width, height), we should return the center point
            if secondArg is None:
                return pyautogui.center(firstArg)
            else:
                raise pyautogui.PyAutoGUIException(
                    "When passing a sequence for firstArg, secondArg must not be passed "
                    f"and default to None (received {secondArg!r})."
                )
        else:
            raise pyautogui.PyAutoGUIException(
                "The supplied sequence must have exactly 2 or exactly 4 elements "
                f"({len(firstArg)} were received)."
            )
    else:
        return Point(int(firstArg), int(secondArg))  # firstArg and secondArg are just x and y number values


# ---- Path polynomial helpers moved from api.py ----

def _fit_quartic(points):
    """
    Fit a 4-th degree polynomial through 5 (t, value) pairs.

    Parameters
    ----------
    points : list[tuple[float, float]]
        Exactly five (t_i, v_i) pairs where 0 ≤ t_i ≤ 1.

    Returns
    -------
    tuple[float, float, float, float, float]
        Coefficients (a, b, c, d, e) such that
        v(t) = a*t^4 + b*t^3 + c*t^2 + d*t + e
    """
    if len(points) != 5:
        raise ValueError("Need exactly 5 control points for a 4th-degree fit")

    t = np.array([p[0] for p in points], dtype=float)
    v = np.array([p[1] for p in points], dtype=float)

    # Build the Vandermonde matrix for degree-4 terms
    V = np.vstack([t**4, t**3, t**2, t, np.ones_like(t)]).T  # shape (5, 5)

    # Solve V * coeffs = v -> coeffs = (a, b, c, d, e)
    coeffs = np.linalg.solve(V, v)        # returns a 5-element vector

    return tuple(coeffs)                  # (a, b, c, d, e)


def _build_mouse_path_polynomials(p_start, p_dest):
    """
    Create 3 jittered intermediate points between p_start and p_dest,
    fit separate quartic polynomials x(t) and y(t) through the 5 points,
    and return their coefficients.

    Parameters
    ----------
    p_start : tuple[float, float]  # (x0, y0)
    p_dest  : tuple[float, float]  # (x4, y4)

    Returns
    -------
    ((ax, bx, cx, dx, ex), (ay, by, cy, dy, ey))
        Coefficients for x(t) and y(t), where t is in {0, 1, 2, 3, 4}.
    """
    x0, y0 = p_start
    x4, y4 = p_dest

    # --- 1. base equally-spaced points (25%, 50%, 75%) ---
    v_x, v_y = x4 - x0, y4 - y0
    base_pts = [
        (x0 + 0.25 * v_x, y0 + 0.25 * v_y),
        (x0 + 0.50 * v_x, y0 + 0.50 * v_y),
        (x0 + 0.75 * v_x, y0 + 0.75 * v_y),
    ]

    # --- 2. jitter each base point by up to dist/6 in x and y ---
    dist = math.hypot(v_x, v_y) / 6.0
    jittered = [
        (bx + random.uniform(-dist, dist), by + random.uniform(-dist, dist))
        for bx, by in base_pts
    ]

    # --- 3. assemble full control-point list in original order ---
    pts = [p_start, *jittered, p_dest]

    # --- 4. assign t = 0..4 and fit polynomials ---
    t_values = [0, 1, 2, 3, 4]
    x_ctrl = list(zip(t_values, [p[0] for p in pts]))
    y_ctrl = list(zip(t_values, [p[1] for p in pts]))

    coeff_x = _fit_quartic(x_ctrl)   # (ax, bx, cx, dx, ex)
    coeff_y = _fit_quartic(y_ctrl)   # (ay, by, cy, dy, ey)

    return coeff_x, coeff_y


# ---------- polynomial evaluator ----------
def _eval_poly(coeffs, t):
    """Horner-style evaluation of a*t^4 + b*t^3 + c*t^2 + d*t + e."""
    a, b, c, d, e = coeffs
    return (((a * t + b) * t + c) * t + d) * t + e


def _paths(coeffsX, coeffsY, t):
    return (_eval_poly(coeffsX, t * 4), _eval_poly(coeffsY, t * 4))


# ---------- main mover ----------
def _move_mouse_poly(driver, dest_x, dest_y, total_dur=0.45, titlebar_h=80, x_offset=20):
    """
    Move the real cursor from its current position to (dest_x, dest_y) inside
    the browser window, following a randomised quartic path.

    dest_x, dest_y: coordinates inside the page viewport (CSS pixels)
    total_dur: total time for the glide, in seconds
    """
    # 1) Window offset: translate page coords to absolute screen coords.
    win_pos = driver.get_window_position()
    abs_dest = (
        int(win_pos["x"] + dest_x + x_offset),
        int(win_pos["y"] + titlebar_h + dest_y),
    )

    print("abs_dest", abs_dest)

    # 2) Current cursor pos (screen coords)
    abs_start = pyautogui.position()

    # 3) Build quartic path coeffs in screen space
    poly_x, poly_y = _build_mouse_path_polynomials(abs_start, abs_dest)

    path = partial(_paths, poly_x, poly_y)

    # 5) Sample t from 0 to 4 (matching our 5-point construction).
    moveAlongPath(path, abs_dest[0], abs_dest[1], total_dur)


def _mouse_jitter(center_x, center_y, radius=10, duration=2.0, interval=0.05, break_func=None):
    """
    Moves the mouse around randomly within a given radius of a center point.

    :param center_x: X coordinate of the center point.
    :param center_y: Y coordinate of the center point.
    :param radius: Maximum distance from center point in pixels.
    :param duration: Total time to jitter in seconds.
    :param interval: Time between each small move in seconds.
    """
    start_time = time.time()
    while time.time() - start_time < duration:
        if (break_func is not None) and break_func():
            break
        # Pick a random angle and distance within the radius
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius)

        # Calculate new position
        new_x = center_x + dist * math.cos(angle)
        new_y = center_y + dist * math.sin(angle)

        pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.02, 0.08))
        time.sleep(interval)
