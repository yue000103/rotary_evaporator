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
        :param username: 用户名
        :param password: 密码
        :param base_url_key: 在 com_config.yaml 里定义的 base_url key (默认为 "default")
        :param mock: 是否启用 mock 模式
        """
        self.username = "rw"
        self.password = "Sg3v2QtR"
        self.base_url = get_base_url("xuanzheng")  # 根据 key 选择 base_url
        self.mock = mock
        self.running = False  # 心跳线程运行控制标志
        self.heartbeat_thread = None

        credentials = f"{self.username}:{self.password}"
        self.encoded_credentials = base64.b64encode(credentials.encode()).decode()
        print(f"Initialized ConnectionController with base_url: {self.base_url}")
        com_logger.info(f"Initialized ConnectionController with base_url: {self.base_url}")



        if not self.mock:
            self.driver = self._initialize_driver()
            self._start_heartbeat()  # 自动启动心跳

    def _start_heartbeat(self):
        """启动心跳线程"""
        self.running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True  # 守护线程（主线程退出时自动结束）
        )
        self.heartbeat_thread.start()
        com_logger.info("Heartbeat thread started")

    def _heartbeat_loop(self):
        """心跳线程循环"""
        while self.running:
            try:
                response = self.send_request("/api/v1/process", method='GET')
                # print(f"Heartbeat received: {response[:50]}...")
                com_logger.debug(f"Heartbeat received: {response[:50]}...")  # 截短日志
            except Exception as e:
                com_logger.error(f"Heartbeat failed: {str(e)}")

            # 等待5秒（包含提前退出的检查）
            for _ in range(50):
                if not self.running:
                    return
                time.sleep(0.1)

    def _initialize_driver(self):
        print("--------------1-------------------")

        chrome_options = Options()
        print("--------------2-------------------")

        chrome_options.add_argument("--headless")  # 无界面模式
        print("--------------3-------------------")

        chrome_options.add_argument("--ignore-certificate-errors")
        print(chrome_options)
        return webdriver.Chrome(options=chrome_options)

    def _send_request(self, endpoint, method='GET', data=None):
        """ 发送 HTTP 请求 """
        get_url = f"https://{self.username}:{self.password}@{self.base_url}{endpoint}"  # 组合 URL
        put_url = f"https://{self.base_url}{endpoint}"
        # print("get_url", get_url)
        # print("put_url", put_url)

        if self.mock:
            log_message = f"[Mock Mode] {method} request to {get_url} with data: {data}"
            com_logger.info(log_message)
            return "Mock Response"

        if method == 'GET':
            # print("full_url",get_url)
            # self.driver.get("https://rw:Sg3v2QtR@192.168.1.20/api/v1/info")
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
            print("put",json.dumps(data))

            return self.driver.execute_script(script)


    def send_request(self, endpoint, method='GET', data=None):
        get_url = f"https://{self.username}:{self.password}@{self.base_url}{endpoint}"
        put_url = f"https://{self.base_url}{endpoint}"

        if self.mock:
            log_message = f"[Mock Mode] {method} request to {get_url} with data: {data}"
            com_logger.info(log_message)
            return "Mock Response"

        if method == 'GET':
            for attempt in range(3):  # 最多重试3次
                try:
                    self.driver.get(get_url)
                    # 每次都重新查找元素，避免 stale
                    body = self.driver.find_element("tag name", "body")
                    page_text = body.text
                    com_logger.info(page_text)
                    return page_text
                except (StaleElementReferenceException, NoSuchElementException) as e:
                    print(f"第 {attempt + 1} 次尝试失败: {e}, 正在重试...")
                    time.sleep(1)

            raise RuntimeError("多次重试后仍未成功获取页面内容")

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
        """关闭连接和心跳"""
        if not self.mock:
            self.running = False  # 停止心跳循环

            if self.heartbeat_thread and self.heartbeat_thread.is_alive():
                self.heartbeat_thread.join(timeout=2)  # 等待线程结束

            if self.driver:
                self.driver.quit()
                com_logger.info("Browser driver closed")

        com_logger.info("Connection controller shutdown complete")


if __name__ == "__main__":
    xuancheng_com = ConnectionController(mock=False)  # 创建实例时会自动启动心跳

    # 主线程可以做其他事情...
    time.sleep(20)

    xuancheng_com.close()  # 关闭时会自动停止心跳
