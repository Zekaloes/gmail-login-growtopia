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
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

output = {
    "status": "success",
    "token": "token",
    "message": "optional message"
}

urls = {
    'accounts.google.com/v3/signin/challenge/recaptcha',
    'accounts.google.com/v3/signin/challenge/pwd',
    'accounts.google.com/signin/oauth/id?authuser',
    'login.growtopiagame.com/player/growid/logon-name'
}


def url_changed():
    def _url_changed(driver):
        for url in urls:
            if url in driver.current_url:
                return True
        return False

    return _url_changed


global process

def generate_username(length=8):
    vowels = "aeiou"
    consonants = "".join(set(string.ascii_lowercase) - set(vowels))
    numbers = string.digits

    def generate_segment():
        segment_length = random.randint(2, 4)
        return ''.join(random.choice(consonants) + random.choice(vowels) for _ in range(segment_length))

    username = ''.join(generate_segment() for _ in range(length // 2))
    username = (username + ''.join(random.choice(numbers) for _ in range(length - len(username))))[:length]

    username = ''.join(random.sample(username, len(username)))
    return username


def captcha_check(driver):
    try:
        if "accounts.google.com/v3/signin/challenge/recaptcha" in driver.current_url:
            reCAPTCHA_frame = WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@title="reCAPTCHA"]'))
            )
            print("Switched to reCAPTCHA frame")

            for _ in range(100):
                if "You are verified" in driver.page_source:
                    print("You are verified")
                    driver.switch_to.default_content()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[text()="Next"]'))
                    ).click()
                    break
                else:
                    print("You are not verified yet. Retrying...")
                    time.sleep(1)
            else:
                print("Verification failed after multiple attempts.")
    except TimeoutException as e:
        print("Timeout occurred:", e)
    except NoSuchElementException as e:
        print("Element not found:", e)
    except Exception as e:
        print("An error occurred:", e)


def handle_urls(driver):
    if 'accounts.google.com/signin/oauth/id?authuser' in driver.current_url:
        WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[3]/div/div/div[2]/div/div/button/span'))
                    ).click()
    elif 'accounts.google.com/v3/signin/challenge/recaptcha' in driver.current_url:
        captcha_check(driver)
        time.sleep(5)
    elif 'login.growtopiagame.com/player/growid/logon-name' in driver.current_url:
        time.sleep(4)
        try:

            token_pattern = r'"token":"(.*?)"'
            match = re.search(token_pattern, driver.page_source)
            if match:
                token = match.group(1)
                driver.close()
                driver.quit()

                output['status'] = 'success'
                output['token'] = token
                output_json = json.dumps(output)

                with open("autologin_tools/data.txt", "w") as file:
                    file.write(output_json)

                print(output_json)
            else:
                driver.close()
                driver.quit()
                output['status'] = 'failed'
                output_json = json.dumps(output)

                print(output_json)

        except Exception as e:
            print(e)
            while True:
                username = generate_username()

                time.sleep(10)
                elements = driver.find_elements(By.XPATH,
                                                '//*[@id="modalShow"]/div/div/div/div/section/div/div[2]/ul/li')

                found_message = False
                for element in elements:
                    if element.text == 'What kind of name is that? Kids play this too, ya know.':
                        found_message = True
                        break

                if not found_message:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="login-name"]'))
                    ).send_keys(username)
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="modalShow"]/div/div/div/div/section/div/div[2]/div/form/div[2]/input'))
                    ).click()
                    time.sleep(5)
                    break

            response_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "/html/body"))
            )

            token_pattern = r'"token":"(.*?)"'
            match = re.search(token_pattern, driver.page_source)
            if match:
                token = match.group(1)
                driver.close()
                driver.quit()

                output['status'] = 'success'
                output['token'] = token
                output_json = json.dumps(output)

                with open("autologin_tools/data.txt", "w") as file:
                    file.write(output_json)

                print(output_json)
            else:
                driver.close()
                driver.quit()
                output['status'] = 'failed'
                output_json = json.dumps(output)

                print(output_json)
    else:
        tries = 10
        while True:
            try:
                tries = tries - 1
                response_element = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/center/h1"))
                )
                response_text = response_element.text
                if '502' in response_text:
                    driver.refresh()
                else:
                    if 'login.growtopiagame.com/player/growid/logon-name' in driver.current_url:
                        handle_urls(driver)
                    return
            except Exception as e:
                if 'login.growtopiagame.com/player/growid/logon-name' in driver.current_url:
                    handle_urls(driver)
                return

def find_available_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            if result != 0:
                return port
    raise Exception("No available ports found in the given range")

def main():
    global data, process
    if len(sys.argv) < 2:
        sys.exit(1)

    json_arg = sys.argv[1]
    with open("autologin_tools/data.txt", "w") as file:
        file.write(json_arg)

    try:
        with open("autologin_tools/data.txt", "r") as file:
            json_arg = file.read()
    except FileNotFoundError:
        pass

    try:
        data = json.loads(json_arg)
    except json.JSONDecodeError as e:
        output['status'] = 'failed'
        output["message"] = 'fail json'
        output_json = json.dumps(output)

        print(output_json)

    global email

    url = data.get("url")
    email = data.get("mail")
    password = data.get("pass")
    headless = data.get("headless")
    proxy = data.get("proxy")

    usernames = email.split('@')[0]
    try:
        with open('autologin_tools/email.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                email_password = line.strip()
                emails = email_password.split('|')[0]
                if emails.split('@')[0] == usernames:
                    email = emails
    except Exception as e:
        pass

    try:
        with open('autologin_tools/bypass.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                proxy_details = line.strip()
                proxys = proxy_details.split('@')
                if proxy in proxy_details:
                    proxy = proxys[1]
    except Exception as e:
        pass

    chrome_options = uc.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless")

    if len(proxy) > 0:
        proxy_parts = proxy.split(':')
        if len(proxy_parts) == 2:
            chrome_options.add_argument(f"--proxy-server=socks5://{proxy}")
        elif len(proxy_parts) == 4:
            proxyexe_path = os.path.abspath("autologin_tools/ProxySupport/ProxySupport.exe")
            localport = find_available_port(8001, 65535)
            command = fr'{proxyexe_path} -L socks5://:{localport} -F socks5://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}'

            process = subprocess.Popen(
                ['cmd', '/c', command],
                shell=True
            )

            chrome_options.add_argument(f"--proxy-server=socks5://127.0.0.1:{localport}")

    extension_path = os.path.abspath("autologin_tools/extension")

    if os.path.exists(extension_path):
        chrome_options.add_argument(f"--load-extension={extension_path}")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=chrome_options)

    try:
        time.sleep(2)
        driver.get(url)

        handle_urls(driver)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "identifierId"))).send_keys(
            email + Keys.ENTER)

        try:
            WebDriverWait(driver, 10).until(url_changed())
        except Exception:
            pass

        handle_urls(driver)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "Passwd"))).send_keys(
            password + Keys.ENTER)

        try:
            WebDriverWait(driver, 10).until(url_changed())
        except Exception:
            pass

        handle_urls(driver)

    except Exception as e:
        output['status'] = 'failed'
        output_json = json.dumps(output)

        print(output_json)
        driver.close()
        driver.quit()


main()
