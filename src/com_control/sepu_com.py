import requests
import json
from datetime import datetime
import time
from src.uilt.yaml_control.setup import get_base_url


class SepuCom:
    def __init__(self):
        """
        SepuCom，设置基本的API URL。

        参数:
        base_url (str): API的基本URL，例如 "http://localhost:5000"
        """
        self.base_url = get_base_url("sepu_com")
        self.method_id = 0

    def send_post_request(self, endpoint: str, payload: dict) -> dict:
        """
        发送POST请求到指定的API接口。

        参数:
        endpoint (str): API的具体路径，如 "/status/init_device"
        payload (dict): 请求负载，作为JSON传递

        返回:
        dict: 请求的响应数据
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload)

        # 检查请求是否成功
        if response.status_code == 200:
            return response.json()  # 返回响应的JSON数据
        else:
            error_message = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            try:
                error_response = response.json()
                error_message["detailed_error"] = json.dumps(error_response, indent=2)
            except ValueError:
                error_message["detailed_error"] = "无法解析错误响应的JSON内容。"
            return error_message

    def send_get_request(self, endpoint: str) -> dict:
        """
        发送GET请求到指定的API接口。

        参数:
        endpoint (str): API的具体路径，如 "/method/only/operate"

        返回:
        dict: 请求的响应数据
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            return response.json()  # 返回响应的JSON数据
        else:
            error_message = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            try:
                error_response = response.json()
                error_message["detailed_error"] = json.dumps(error_response, indent=2)
            except ValueError:
                error_message["detailed_error"] = "无法解析错误响应的JSON内容。"
            return error_message