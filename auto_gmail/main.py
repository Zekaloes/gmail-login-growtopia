import ctypes
import os
import random
import re
import socket
import string
import subprocess
import sys
import json
import time

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
DEBUG_FILE = "autologin_tools/debug.txt"
OUTPUT_FILE = "autologin_tools/data.txt"
PROXY_SUPPORT_PATH = "autologin_tools/ProxySupport/ProxySupport.exe"
EXTENSION_PATH = os.path.abspath("autologin_tools/extension")

OUTPUT = {
    "status": STATUS_SUCCESS,
    "token": "token",
    "message": "optional message"
}

TARGET_URLS = [
    'accounts.google.com/v3/signin/challenge/recaptcha',
    'accounts.google.com/v3/signin/challenge/pwd',
    'accounts.google.com/signin/oauth/id?authuser',
    'login.growtopiagame.com/player/growid/logon-name'
]

def has_target_url_changed(driver):
    """Check if the current URL of the driver matches any of the target URLs."""
    for url in TARGET_URLS:
        if url in driver.current_url:
            return True
    return False

def generate_username(length=8):

    vowels = "aeiou"
    consonants = "".join(set(string.ascii_lowercase) - set(vowels))

    first_char = random.choice(string.ascii_uppercase)
    remaining_chars = []
    for i in range(length - 1):
        if i % 2 == 0:
            remaining_chars.append(random.choice(consonants))
        else:
            remaining_chars.append(random.choice(vowels))

    username = first_char + ''.join(remaining_chars)
    return username

def solve_captcha(driver):
    """Handle reCAPTCHA challenges if present in the current URL."""
    try:
        if "accounts.google.com/v3/signin/challenge/recaptcha" in driver.current_url:
            recaptcha_frame = WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@title="reCAPTCHA"]'))
            )

            for _ in range(100):
                if "You are verified" in driver.page_source:
                    driver.switch_to.default_content()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[text()="Next"]'))
                    ).click()
                    break
                else:
                    time.sleep(1)
    except TimeoutException as e:
        pass
    except NoSuchElementException as e:
        pass
    except Exception as e:
        pass

def handle_target_urls(driver):
    """Handle different target URLs and perform respective actions."""
    time.sleep(2)
    if 'accounts.google.com/signin/oauth/id?authuser' in driver.current_url:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[3]/div/div/div[2]/div/div/button/span'))
        ).click()
    elif 'accounts.google.com/speedbump' in driver.current_url:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="confirm"]'))
        ).click()
        try:
            WebDriverWait(driver, 10).until(has_target_url_changed)
        except Exception:
            pass

        time.sleep(8)
    elif 'accounts.google.com/v3/signin/challenge/recaptcha' in driver.current_url:
        solve_captcha(driver)
        time.sleep(5)
    elif 'login.growtopiagame.com/player/growid/logon-name' in driver.current_url:
        time.sleep(4)
        try:
            if not ('Choose your name in Growtopia' in driver.page_source):
                token_pattern = r'"token":"(.*?)"'
                match = re.search(token_pattern, driver.page_source)
                if match:
                    token = match.group(1)
                    OUTPUT['token'] = token
                    save_output(OUTPUT)
                else:
                    OUTPUT['status'] = STATUS_FAILED
                    save_output(OUTPUT)
            else:
                generate_and_enter_username(driver)
                wait_for_token(driver)
        except Exception as e:
            generate_and_enter_username(driver)
            wait_for_token(driver)
    else:
        
        retry_page_loading(driver)

def retry_page_loading(driver):
    """Retry loading the page if certain conditions are met."""
    tries = 10
    while tries > 0:
        tries -= 1
        try:
            response_element = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/center/h1"))
            )
            response_text = response_element.text
            if '502' in response_text:
                driver.refresh()
            else:
                if 'login.growtopiagame.com/player/growid/logon-name' in driver.current_url:
                    handle_target_urls(driver)
                return
        except Exception as e:
            if 'login.growtopiagame.com/player/growid/logon-name' in driver.current_url:
                handle_target_urls(driver)
            return

def generate_and_enter_username(driver):
    """Generate a new username and enter it in the login form."""
    while True:
        username = generate_username()
        time.sleep(6)
        elements = driver.find_elements(By.XPATH, '//*[@id="modalShow"]/div/div/div/div/section/div/div[2]/ul/li')

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="login-name"]'))
        ).send_keys(username)

        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="modalShow"]/div/div/div/div/section/div/div[2]/div/form/div[2]/input'))
        ).click()
        time.sleep(5)

        found_message = any(element.text == 'What kind of name is that? Kids play this too, ya know.' for element in elements)

        if not found_message:
            break

def wait_for_token(driver):
    """Wait for the token to be available in the page source."""
    response_element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "/html/body"))
    )

    token_pattern = r'"token":"(.*?)"'
    match = re.search(token_pattern, driver.page_source)
    if match:
        token = match.group(1)
        OUTPUT['token'] = token
        save_output(OUTPUT)
    else:
        OUTPUT['status'] = STATUS_FAILED
        save_output(OUTPUT)

def get_screen_size():
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    return screen_width, screen_height

def find_available_port(start_port, end_port):
    """Find an available port within the specified range."""
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            if result != 0:
                return port
    raise Exception("No available ports found in the given range")

def save_output(output):
    """Save the output to the specified file."""
    with open(OUTPUT_FILE, "w") as file:
        output_json = json.dumps(output)
        file.write(output_json)
    print(output_json)

def save_debug(output):
    """Save the debug errors to the specified file."""
    with open(DEBUG_FILE, "w") as file:
        file.write(str(output))

def main():
    global process, cmd_process
    try:
        '''if len(sys.argv) < 2:
            sys.exit(1)

        json_arg = sys.argv[1]
        with open(OUTPUT_FILE, "w") as file:
            file.write(json_arg)'''

        try:
            with open(OUTPUT_FILE, "r") as file:
                json_arg = file.read()
        except FileNotFoundError:
            pass

        try:
            data = json.loads(json_arg)
        except json.JSONDecodeError:
            OUTPUT['status'] = STATUS_FAILED
            OUTPUT["message"] = 'fail json'
            save_output(OUTPUT)
            return

        url = data.get("url")
        email = data.get("mail")
        password = data.get("pass")
        headless = data.get("headless")
        proxy = data.get("proxy")

        try:
            with open('autologin_tools/email.txt', 'r') as file:
                lines = file.readlines()
                for line in lines:
                    email_password = line.strip()
                    emails = email_password.split('|')[0]
                    if emails.split('@')[0] == email.split('@')[0]:
                        email = emails
        except Exception:
            pass

        try:
            with open('autologin_tools/bypass.txt', 'r') as file:
                lines = file.readlines()
                for line in lines:
                    proxy_details = line.strip()
                    proxys = proxy_details.split('@')
                    if proxy in proxy_details:
                        proxy = proxys[1]
        except Exception:
            pass

        chrome_options = uc.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless")

        if proxy:
            proxy_parts = proxy.split(':')
            if len(proxy_parts) == 2:
                chrome_options.add_argument(f"--proxy-server=socks5://{proxy}")
            elif len(proxy_parts) == 4:
                proxy_path = os.path.abspath(PROXY_SUPPORT_PATH)
                local_port = find_available_port(8001, 65535)
                command = fr'{proxy_path} -L socks5://:{local_port} -F socks5://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}'

                cmd_process = subprocess.Popen(f'cmd /c {command}', stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, shell=True)
                chrome_options.add_argument(f"--proxy-server=socks5://127.0.0.1:{local_port}")

        if os.path.exists(EXTENSION_PATH):
            chrome_options.add_argument(f"--load-extension={EXTENSION_PATH}")

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = uc.Chrome(options=chrome_options, driver_executable_path=ChromeDriverManager().install())


    except Exception as e:
        save_debug(e)
        sys.exit(1)

    try:
        time.sleep(2)
        driver.get(url)

        driver.set_window_size(800,600)

        screen_width, screen_height = get_screen_size()
        x = random.randint(0, screen_width - 800)
        y = random.randint(0, screen_height - 600)
        driver.set_window_position(x, y)

        handle_target_urls(driver)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        ).send_keys(email + Keys.ENTER)

        try:
            WebDriverWait(driver, 10).until(has_target_url_changed)
        except Exception:
            pass

        handle_target_urls(driver)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        ).send_keys(password + Keys.ENTER)

        try:
            WebDriverWait(driver, 10).until(has_target_url_changed)
        except Exception:
            pass

        handle_target_urls(driver)

    except Exception as e:
        save_debug(e)
        OUTPUT['status'] = STATUS_FAILED
        save_output(OUTPUT)
        driver.close()
        driver.quit()

    finally:
        if driver:
            driver.close()
            driver.quit()

if __name__ == "__main__":
    main()
