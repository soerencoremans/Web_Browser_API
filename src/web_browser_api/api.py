import random
import shutil
import string
import subprocess
import sys
import time

from faker import Faker
import pyautogui
import pytesseract
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc

from ._keyboard import _switch_to_us, _xkb_apply, _xkb_query
from .driver import get_driver
from .move_mouse import _move_mouse_poly

fake = Faker()


def switch_to_latest_tab(driver):
    try:
        driver.switch_to.window(driver.window_handles[-1])
        print("Switched to the latest tab.")
    except Exception as e:
        print(f"Error switching tabs: {e}")


def open_new_tab(driver, url="about:blank", timeout=5):
    """
    Open a new tab in a Chrome session, switch to it, and return its handle.
    Uses Selenium 4 API first, then falls back to a keyboard shortcut.
    """
    old_handles = set(driver.window_handles)

    try:
        driver.switch_to.new_window("tab")
        if url and url != "about:blank":
            driver.get(url)
        return driver.current_window_handle
    except WebDriverException:
        pass

    active = driver.switch_to.active_element
    try:
        active.send_keys(Keys.CONTROL + "t")
        WebDriverWait(driver, timeout).until(
            lambda d: len(set(d.window_handles) - old_handles) == 1
        )
    except TimeoutException:
        active.send_keys(Keys.COMMAND + "t")
        WebDriverWait(driver, timeout).until(
            lambda d: len(set(d.window_handles) - old_handles) == 1
        )

    new_handles = set(driver.window_handles) - old_handles
    if not new_handles:
        raise TimeoutException("New tab was not opened.")

    new_handle = new_handles.pop()
    driver.switch_to.window(new_handle)
    if url and url != "about:blank":
        driver.get(url)
    return new_handle


def close_current_tab(driver, switch_to_last: bool = True):
    """
    Closes the currently active tab.

    :param driver: The Selenium WebDriver instance
    :param switch_to_last: If True, switch focus to the last remaining tab
    """
    driver.close()

    # If there are tabs left and we want to switch, do so
    if driver.window_handles and switch_to_last:
        driver.switch_to.window(driver.window_handles[-1])


def focus_chrome_window():
    # This will search for a Chrome window and activate it
    subprocess.run(
        ["xdotool", "search", "--onlyvisible", "--class", "chrome", "windowactivate"],
        check=False,
    )
    time.sleep(0.2)  # short delay to ensure focus


def generate_password():
    lowers = random.choices(string.ascii_lowercase, k=5)
    uppers = random.choices(string.ascii_uppercase, k=5)
    digits = random.choices(string.digits, k=5)
    symbols = random.choices("!@#$%&*", k=2)

    all_chars = lowers + uppers + digits + symbols
    random.shuffle(all_chars)
    return "".join(all_chars)


def generate_bot_identity():
    first_name = fake.first_name()
    last_name = fake.last_name()
    username = f"{first_name.lower()}.{last_name.lower()}" + "".join(
        random.choices(string.digits, k=8)
    )
    password = generate_password()

    # Faker provides random dates of birth
    birthdate_obj = fake.date_of_birth(minimum_age=18, maximum_age=80)
    birthdate = {
        "year": birthdate_obj.year,
        "month": birthdate_obj.month,
        "day": birthdate_obj.day,
    }

    return {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "password": password,
        "birthdate": birthdate,
    }


def type_like_human(text):
    """
    Type text into the currently focused element as real keypresses.
    Temporarily switches keyboard layout to US and restores afterwards.
    """
    if sys.platform != "linux":
        raise RuntimeError("This layout switcher currently supports Linux/X11 only.")
    if not shutil.which("setxkbmap"):
        raise RuntimeError("setxkbmap not found. Install it (e.g., sudo apt install x11-xkb-utils).")

    original = _xkb_query()
    try:
        _switch_to_us()
        time.sleep(0.15)  # tiny settle time after layout change

        for char in text:
            if char == "\n":
                pyautogui.press("enter")
            elif char == "\t":
                pyautogui.press("tab")
            else:
                pyautogui.write(char)  # US layout: Shift+2 = @, etc.
            time.sleep(random.uniform(0.05, 0.15))
    finally:
        try:
            _xkb_apply(original)
        except Exception as e:
            # Do not crash on restore; print a helpful hint instead.
            print(
                f"[WARN] Failed to restore keyboard layout: {e}. "
                f"You can manually restore with: setxkbmap {original.get('layout', 'us')}"
            )


def human_pause(min_sec=0.3, max_sec=1.2):
    time.sleep(random.uniform(min_sec, max_sec))


def move_mouse(driver: uc.Chrome, x, y, total_dur=1.5, titlebar_h=108, x_offset=20):
    _move_mouse_poly(driver, x, y, total_dur=total_dur, titlebar_h=titlebar_h, x_offset=x_offset)


def get_element_center(element):
    # Get element's position and size from Selenium
    location = element.location
    size = element.size

    # Middle point in browser coordinate space
    center_x = location["x"] + size["width"] / 2
    center_y = location["y"] + size["height"] / 2

    return center_x, center_y


def get_element_click_point(element, shrink_ratio=0.2):
    """
    Return a random point inside an element's centered hitbox.

    shrink_ratio reduces width and height before sampling. The default 0.2
    samples within the centered 80% of the element.
    """
    if not 0 <= shrink_ratio < 1:
        raise ValueError("shrink_ratio must be at least 0 and less than 1.")

    location = element.location
    size = element.size

    inset_x = size["width"] * shrink_ratio / 2
    inset_y = size["height"] * shrink_ratio / 2

    min_x = location["x"] + inset_x
    max_x = location["x"] + size["width"] - inset_x
    min_y = location["y"] + inset_y
    max_y = location["y"] + size["height"] - inset_y

    return random.uniform(min_x, max_x), random.uniform(min_y, max_y)


def click_element(driver, element, titlebar_h=108, x_offset=20):
    posx, posy = get_element_click_point(element)
    move_mouse(driver, posx, posy, titlebar_h=titlebar_h, x_offset=x_offset)
    pyautogui.click()


def click_and_hold_element(driver, element, seconds=2, titlebar_h=108, x_offset=20):
    posx, posy = get_element_click_point(element)
    move_mouse(driver, posx, posy, titlebar_h=titlebar_h, x_offset=x_offset)
    pyautogui.mouseDown()
    try:
        time.sleep(seconds)
    finally:
        pyautogui.mouseUp()


def click_and_hold_pos(driver, pos, seconds=2, break_func=None, titlebar_h=108, x_offset=20):
    move_mouse(driver, pos[0], pos[1], titlebar_h=titlebar_h, x_offset=x_offset)
    pyautogui.mouseDown()
    try:
        if break_func is not None:
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if not break_func():
                    break
                time.sleep(min(1 / 3, max(0, deadline - time.monotonic())))
        else:
            time.sleep(seconds)
    finally:
        pyautogui.mouseUp()


def extract_text_from_chrome_window(driver):
    # Get browser window position/size
    rect = driver.get_window_rect()
    screenshot = pyautogui.screenshot(
        region=(rect["x"], rect["y"], rect["width"], rect["height"])
    )

    text = pytesseract.image_to_string(screenshot)
    return text


if __name__ == "__main__":
    driver = get_driver()
    move_mouse(driver, 0, 0, total_dur=2)
    print(pyautogui.position())
