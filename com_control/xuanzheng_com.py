import base64
import json
import time
import yaml
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

from service_control.logs_control.setup import com_logger

script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, '../config/com_config.yaml')


# 设置日志
# logging.basicConfig(filename='mock_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 读取 com_control.yaml
with open(config_path, "r") as file:
    config = yaml.safe_load(file)


def get_base_url():
    return config.get("base_url", "https://192.168.1.20")


class ConnectionController:
    def __init__(self, username, password, base_url=None, mock=False):
        self.username = username
        self.password = password
        self.base_url = base_url or get_base_url()
        self.mock = mock

        credentials = f"{username}:{password}"
        self.encoded_credentials = base64.b64encode(credentials.encode()).decode()

        if not self.mock:
            self.driver = self._initialize_driver()

    def _initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--ignore-certificate-errors")
        return webdriver.Chrome(options=chrome_options)

    def send_request(self, endpoint, method='GET', data=None):
        if self.mock:
            log_message = f"[Mock Mode] {method} request to {endpoint} with data: {data}"
            com_logger.info(log_message)
            return "Mock Response"

        if method == 'GET':
            self.driver.get(f"{self.base_url}{endpoint}")
            return self.driver.find_element("tag name", "body").text
        elif method == 'PUT':
            script = f'''
            return fetch("{self.base_url}{endpoint}", {{
              method: 'PUT',
              headers: {{
                'Content-Type': 'application/json',
                'Authorization': 'Basic {self.encoded_credentials}'
              }},
              body: JSON.stringify({json.dumps(data)})
            }}).then(response => response.text());
            '''
            return self.driver.execute_script(script)

    def close(self):
        if not self.mock:
            self.driver.quit()