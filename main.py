import os
import time
import random
import secrets
import base64
import faker
import socket
import threading
import zipfile
import shutil
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import undetected_chromedriver as uc

from email_api import get_email, get_code, cancel_mail

lock = threading.Lock()

faker = faker.Faker(locale='tr-TR')

resolution = ['1366x768', '1600x900', '1920x1080', '2560x1440', '3840x2160', '1280x800', '1920x1200', '1440x900']


# lang = 'tr'
# country = 'tr-TR'

def get_random_port():
    while True:
        rnd_port = random.randint(10000, 60000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", rnd_port)) != 0:
                return rnd_port

def get_chromedriver(proxy=None, thread_id=0):
    try:
        chrome_options = uc.ChromeOptions()

        chrome_options.add_argument("--lang=tr")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--remote-debugging-port={get_random_port()}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)

        # if os.path.exists('extensiones/all_fingerprint'):
        #    chrome_options.add_argument(f"--load-extension=extensiones/all_fingerprint")

        pluginfile = ""

        if proxy and '@' in proxy:
            auth_part, server_part = proxy.split('@')
            proxy_user, proxy_pass = auth_part.split(':')
            proxy_host, proxy_port = server_part.split(':')

            manifest_json = """{
                "name": "Chrome Proxy",
                "description": "Use proxy with auth",
                "version": "1.0.0",
                "manifest_version": 3,
                "permissions": [
                    "proxy",
                    "storage",
                    "scripting",
                    "tabs",
                    "unlimitedStorage",
                    "webRequest",
                    "webRequestAuthProvider"
                ],
                "host_permissions": [
                    "<all_urls>"
                ],
                "background": {
                    "service_worker": "background.js"
                },
                "action": {
                    "default_title": "Proxy Extension"
                }
            }"""

            background_js = """chrome.runtime.onInstalled.addListener(() => {
                const config = {
                    mode: "fixed_servers",
                    rules: {
                        singleProxy: {
                            scheme: "http",
                            host: "%s",
                            port: parseInt(%s)
                        },
                        bypassList: ["localhost"]
                    }
                };

                chrome.proxy.settings.set(
                    {value: config, scope: "regular"},
                    () => {}
                );
            });

            chrome.webRequest.onAuthRequired.addListener(
                function(details) {
                    return {
                        authCredentials: {
                            username: "%s",
                            password: "%s"
                        }
                    };
                },
                {urls: ["<all_urls>"]},
                ["blocking"]
            );""" % (proxy_host, proxy_port, proxy_user, proxy_pass)

            pluginfile = f"extensiones/proxy_auth_plugin_{thread_id}.zip"

            with zipfile.ZipFile(pluginfile, "w") as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)

            pluginfolder = f"extensiones/proxy_auth_plugin_{thread_id}_folder"

            with zipfile.ZipFile(pluginfile, "r") as zip_ref:
                zip_ref.extractall(pluginfolder)

            chrome_options.add_argument("--disable-features=DisableLoadExtensionCommandLineSwitch")
            chrome_options.add_argument(f"--load-extension={os.path.abspath(pluginfolder)}")

        chrome_options.add_argument(
            f"--user-agent={random.choice(agents)}")

        '''prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        '''
        driver = uc.Chrome(options=chrome_options, use_subprocess=True)

        '''
        lang_list = [country, lang, 'en-US', 'en']

        driver.execute_script(f"""
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
            }});

            Object.defineProperty(navigator, 'plugins', {{
                get: () => [1, 2, 3, 4, 5],
            }});

            Object.defineProperty(navigator, 'languages', {{
                get: () => {lang_list},
            }});

            window.chrome = {{
                runtime: {{}},
            }};
        """)'''

        return driver, pluginfile if proxy and '@' in proxy else None
    except Exception as e:
        print(e)

class InstagramAccountCreator:
    def __init__(self, proxy: str = None, thread_id: int = 0):
        self.driver = None
        self.wait = None
        self.proxy = proxy
        self.thread_id = thread_id
        self.pluginfile = None

        self.username = None
        self.name = None
        self.email = None
        self.order_id = None
        self.password = None

    def get_info(self):
        self.name = faker.name().replace('.', '')
        self.email, self.order_id = get_email()
        self.password = secrets.token_hex(8)

    def cleanup(self):
        if self.pluginfile and os.path.exists(self.pluginfile):
            try:
                os.remove(self.pluginfile)
            except Exception as e:
                print(f"Plugin cleanup hatası: {e}")

        plugin_folder = f"{os.path.splitext(self.pluginfile)[0]}_folder"
        if os.path.exists(plugin_folder):
            try:
                shutil.rmtree(plugin_folder)
            except Exception as e:
                print(f"Plugin klasör cleanup hatası: {e}")

    def register(self):
        self.driver, self.pluginfile = get_chromedriver(proxy=self.proxy, thread_id=self.thread_id)
        self.wait = WebDriverWait(self.driver, 20)

        try:
            self.get_info()
            width, height = map(int, random.choice(resolution).split('x'))
            self.driver.set_window_size(width, height)

            self.driver.get("https://www.instagram.com/")
            time.sleep(5)

            try:
                alert = self.driver.switch_to.alert
                alert.dismiss()
                return
            except:
                pass

            if "Instagram" not in self.driver.title:
                return False

            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[href='/accounts/emailsignup/']"))).click()
            time.sleep(3)

            email_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='emailOrPhone']")))
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(0.5)

            password_input = self.driver.find_element(By.XPATH, "//input[@name='password']")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(2)

            try:
                refresh_suggestion = self.wait.until(EC.element_to_be_clickable((By.XPATH, "(//button/span)[2]")))
                refresh_suggestion.click()
                time.sleep(3)
            except:
                print("Öneri yenileme bulunamadı")
                return False

            username_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='username']")
            self.username = username_input.get_attribute("value")

            signup_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            signup_button.click()
            time.sleep(5)

            try:
                month_select = Select(self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[title='Month:'], [title='Ay:']"))))
                month_select.select_by_value(str(random.randint(1, 12)))

                day_select = Select(self.driver.find_element(By.CSS_SELECTOR, "[title='Day:'], [title='Gün:']"))
                day_select.select_by_value(str(random.randint(1, 28)))

                year_select = Select(self.driver.find_element(By.CSS_SELECTOR, "[title='Year:'], [title='Yıl:']"))
                year_select.select_by_value(str(random.randint(1990, 2002)))

                next_button = self.driver.find_element(By.XPATH, "(//button[@type='button'])[2]")
                next_button.click()
                time.sleep(3)
            except Exception as e:
                print(f"Doğum tarihi hatası: {e}")

            try:
                error_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Senin İçin Bir Hesap Oluşturamadık')]")
                if error_element.is_displayed():
                    print("Hesap oluşturma hatası")
                    return
            except:
                pass

            code = get_code(self.order_id)
            print(f"Code: {code}")
            cancel_mail(self.order_id)

            try:
                code_input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='email_confirmation_code']")))
                code_input.clear()
                code_input.send_keys(code)
                time.sleep(1)

                self.driver.find_element(By.XPATH, "(//div[@role='button'])[2]").click()
                time.sleep(10)
            except Exception as e:
                print(f"Kod girişi hatası: {e}")

            for _ in range(10):
                current_url = self.driver.current_url

                if current_url == 'https://www.instagram.com/':
                    time.sleep(8)

                    cookies = self.driver.get_cookies()
                    cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
                    cookie_base64 = base64.b64encode(cookie_str.encode()).decode()

                    account = f"{self.username}:{self.password}:{self.email}:{cookie_base64}"
                    print(f"[{self.username}] Account Created")

                    # self.threads_register()

                    with lock:
                        with open("accounts.txt", "a", encoding="utf-8") as f:
                            f.write(account + "\n")
                    break
                if 'accounts/emailsignup/' in current_url:
                    try:
                        proxy_error = self.driver.find_element(By.XPATH, "//*[contains(text(), 'flagged as an open proxy')]")
                        if proxy_error.is_displayed():
                            print("[!] Bad Proxy")
                            break
                        code_error = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Sorry, there was a problem with your request.') or contains(text(), 'Üzgünüz! Şu anda onay kodunu doğrulamada sorun yaşıyoruz')]")
                        if code_error.is_displayed():
                            print("[!] Bad Proxy")
                            break
                    except:
                        pass

                time.sleep(2)

            # self.driver.delete_all_cookies()
            # self.driver.execute_script("window.localStorage.clear();")
            # self.driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            print(f"Kayıt hatası: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            self.cleanup()

def main(proxy: str, thread_id: int):
    while True:
        try:
            if 'http' in proxy_reset:
                print(requests.get(proxy_reset, verify=False).text)
                time.sleep(3)

            InstagramAccountCreator(proxy=proxy, thread_id=thread_id).register()
        except Exception as e:
            print(f"Thread {thread_id} hatası: {e}")

def get_proxies(filename):
    try:
        with open(filename, "r") as file:
            proxies = [line.strip() for line in file if line.strip()]
            return proxies
    except FileNotFoundError:
        return []

def get_agents(filename):
    try:
        with open(filename, "r") as file:
            agents = [line.strip() for line in file if line.strip()]
            return agents
    except FileNotFoundError:
        return []

if __name__ == '__main__':
    proxy_reset = 'mobil proxy reset link (opsiyonel)'
    proxies = get_proxies("data/proxy.txt")
    agents = get_agents("data/agents.txt")

    threads = []
    for i, p in enumerate(proxies):
        threading.Thread(target=main, args=(p, i)).start()
