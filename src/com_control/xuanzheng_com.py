import base64
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.uilt.logs_control.setup import com_logger
from src.uilt.yaml_control.setup import get_base_url
import threading
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException


class ConnectionController:
    def __init__(self,mock=False):
        """
        :param username: Username
        :param password: Password
        :param base_url_key: base_url key defined in com_config.yaml (default: "default")
        :param mock: Whether to enable mock mode
        """
        self.username = "rw"
        self.password = "Sg3v2QtR"
        self.base_url = get_base_url("xuanzheng")  # 根据 key 选择 base_url
        self.mock = mock
        self.running = False
        self.heartbeat_thread = None

        credentials = f"{self.username}:{self.password}"
        self.encoded_credentials = base64.b64encode(credentials.encode()).decode()
        print(f"Initialized ConnectionController with base_url: {self.base_url}")
        com_logger.info(f"Initialized ConnectionController with base_url: {self.base_url}")

        if not self.mock:
            print("Connecting to Xuanzheng controller...")
            self.driver = self._initialize_driver()
            self._start_heartbeat()

    def _start_heartbeat(self):
        """Start heartbeat thread"""
        self.running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self.heartbeat_thread.start()
        com_logger.info("Heartbeat thread started")

    def _heartbeat_loop(self):
        """Heartbeat loop"""
        while self.running:
            try:
                response = self.send_request("/api/v1/process", method='GET')
                # print(f"Heartbeat received: {response[:50]}...")
                com_logger.debug(f"Heartbeat received: {response[:50]}...")  # 截短日志
            except Exception as e:
                com_logger.error(f"Heartbeat failed: {str(e)}")

            for _ in range(50):
                if not self.running:
                    return
                time.sleep(0.1)

    def _initialize_driver(self):
        max_retries = 3

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} to start Chrome WebDriver...")

                if attempt > 0:
                    self._cleanup_chrome_processes()
                    time.sleep(2)

                chrome_options = Options()

                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--ignore-certificate-errors")
                chrome_options.add_argument("--ignore-ssl-errors")

                import random
                debug_port = random.randint(9000, 9999)
                chrome_options.add_argument(f"--remote-debugging-port={debug_port}")

                import tempfile
                user_data_dir = tempfile.mkdtemp()
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

                print(f"Using debug port: {debug_port}")

                driver = None
                try:
                    from selenium.webdriver.chrome.service import Service

                    service = Service()
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("Successfully started with Selenium built-in ChromeDriver")
                except Exception as e1:
                    print(f"Selenium auto-management failed: {str(e1)}, trying webdriver-manager...")

                    try:
                        from webdriver_manager.chrome import ChromeDriverManager
                        from selenium.webdriver.chrome.service import Service

                        service = Service(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        print("Successfully started with webdriver-manager")
                    except Exception as e2:
                        print(f"webdriver-manager failed: {str(e2)}, trying default method...")

                        driver = webdriver.Chrome(options=chrome_options)
                        print("Successfully started with system default ChromeDriver")

                if driver:
                    print("Chrome WebDriver started successfully!")
                    com_logger.info(f"Chrome WebDriver initialized successfully on attempt {attempt + 1}")
                    return driver

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                com_logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    com_logger.error(f"Failed to initialize Chrome driver after {max_retries} attempts: {str(e)}")
                    raise
                time.sleep(2)

    def _cleanup_chrome_processes(self):
        """Clean up Chrome and ChromeDriver processes"""
        import psutil
        import os
        import signal

        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] in ['chrome', 'chromedriver', 'Google Chrome']:
                    try:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        print(f"Killed process: {proc.info['name']} (PID: {proc.info['pid']})")
                    except:
                        pass
        except:
            pass

    def _send_request(self, endpoint, method='GET', data=None):
        """Send HTTP request"""
        get_url = f"https://{self.username}:{self.password}@{self.base_url}{endpoint}"
        put_url = f"https://{self.base_url}{endpoint}"

        if self.mock:
            log_message = f"[Mock Mode] {method} request to {get_url} with data: {data}"
            com_logger.info(log_message)
            return "Mock Response"

        if method == 'GET':
            self.driver.get(get_url)
            page_text = self.driver.find_element("tag name", "body").text
            com_logger.info(page_text)

            return page_text
        elif method == 'PUT':
            script = f'''
            return fetch("https://192.168.1.20/api/v1/process", {{
              method: 'PUT',
              headers: {{
                'Content-Type': 'application/json',
                'Authorization': 'Basic {self.encoded_credentials}'
              }},
              body: JSON.stringify({json.dumps(data)})
            }}).then(response => response.text());
            '''
            com_logger.info(json.dumps(data))
            print("put", json.dumps(data))

            return self.driver.execute_script(script)


    def send_request(self, endpoint, method='GET', data=None):
        get_url = f"https://{self.username}:{self.password}@{self.base_url}{endpoint}"
        put_url = f"https://{self.base_url}{endpoint}"

        if self.mock:
            log_message = f"[Mock Mode] {method} request to {get_url} with data: {data}"
            com_logger.info(log_message)
            return "Mock Response"

        if method == 'GET':
            for attempt in range(3):
                try:
                    self.driver.get(get_url)
                    body = self.driver.find_element("tag name", "body")
                    page_text = body.text
                    com_logger.info(page_text)
                    return page_text
                except (StaleElementReferenceException, NoSuchElementException) as e:
                    print(f"Attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(1)

            raise RuntimeError("Failed to retrieve page content after multiple retries")

        elif method == 'PUT':
            script = f'''
            return fetch("https://192.168.1.20/api/v1/process", {{
              method: 'PUT',
              headers: {{
                'Content-Type': 'application/json',
                'Authorization': 'Basic {self.encoded_credentials}'
              }},
              body: JSON.stringify({json.dumps(data)})
            }}).then(response => response.text());
            '''
            com_logger.info(json.dumps(data))
            print("put", json.dumps(data))
            return self.driver.execute_script(script)

    def close(self):
        """Close connection and heartbeat"""
        if not self.mock:
            self.running = False

            if self.heartbeat_thread and self.heartbeat_thread.is_alive():
                self.heartbeat_thread.join(timeout=2)

            if self.driver:
                self.driver.quit()
                com_logger.info("Browser driver closed")

        com_logger.info("Connection controller shutdown complete")


if __name__ == "__main__":
    xuancheng_com = ConnectionController(mock=False)

    time.sleep(20)

    xuancheng_com.close()
