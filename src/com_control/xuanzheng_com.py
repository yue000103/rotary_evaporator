import base64
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# from src.uilt.logs_control.setup import com_logger
from src.uilt.yaml_control.setup import get_base_url


class ConnectionController:
    def __init__(self,mock=False):
        """
        :param username: 用户名
        :param password: 密码
        :param base_url_key: 在 com_config.yaml 里定义的 base_url key (默认为 "default")
        :param mock: 是否启用 mock 模式
        """
        self.username = "rw"
        self.password = "Sg3v2QtR"
        self.base_url = get_base_url("xuanzheng")  # 根据 key 选择 base_url
        self.mock = mock

        credentials = f"{self.username}:{self.password}"
        self.encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # com_logger.info(f"Initialized ConnectionController with base_url: {self.base_url}")

        if not self.mock:
            self.driver = self._initialize_driver()

    def _initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无界面模式
        chrome_options.add_argument("--ignore-certificate-errors")
        return webdriver.Chrome(options=chrome_options)

    def send_request(self, endpoint, method='GET', data=None):
        """ 发送 HTTP 请求 """
        get_url = f"https://{self.username}:{self.password}@{self.base_url}{endpoint}"  # 组合 URL
        put_url = f"https://{self.base_url}{endpoint}"
        print("get_url", get_url)
        print("put_url", put_url)

        if self.mock:
            log_message = f"[Mock Mode] {method} request to {get_url} with data: {data}"
            # com_logger.info(log_message)
            return "Mock Response"

        if method == 'GET':
            # print("full_url",get_url)
            self.driver.get("https://rw:Sg3v2QtR@192.168.1.20/api/v1/info")
            page_text = self.driver.find_element("tag name", "body").text

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
            return self.driver.execute_script(script)

    def close(self):
        """ 关闭浏览器驱动 """
        if not self.mock:
            self.driver.quit()
