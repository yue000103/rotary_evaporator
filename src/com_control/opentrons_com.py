import logging
import requests
from src.util.yaml_control.setup import get_base_url
from src.util.logs_control.setup import com_logger


class OpentronsConnection:
    def __init__(self, mock=False):
        """
        Opentrons 机器人通信控制
        :param mock: 是否启用 Mock 模式
        """
        self.host = get_base_url("robot_com")
        self.port = 31950  # Opentrons API 端口
        self.mock = mock
        self.base_url = f"http://{self.host}:{self.port}"

        com_logger.info(f"OpentronsConnection initialized on {self.base_url}")

    def get(self, endpoint):
        """ 发送 GET 请求 """
        if self.mock:
            com_logger.info(f"[Mock Mode] GET {endpoint} simulated response.")
            return {}

        response = requests.get(f"{self.base_url}{endpoint}", headers={"Opentrons-Version": "4"})
        if response.status_code == 200:
            return response.json()
        com_logger.error(f"GET request failed for {endpoint}: {response.json()}")
        return None

    def post(self, endpoint, data):
        """ 发送 POST 请求 """
        if self.mock:
            com_logger.info(f"[Mock Mode] POST {endpoint} with data {data} simulated response.")
            return {}

        response = requests.post(f"{self.base_url}{endpoint}", headers={"Opentrons-Version": "4"}, json=data)
        if response.status_code in [200, 201]:
            return response.json()
        com_logger.error(f"POST request failed for {endpoint}: {response.json()}")
        return None

    def delete(self, endpoint):
        """ 发送 DELETE 请求 """
        if self.mock:
            com_logger.info(f"[Mock Mode] DELETE {endpoint} simulated response.")
            return True

        response = requests.delete(f"{self.base_url}{endpoint}", headers={"Opentrons-Version": "2"})
        if response.status_code == 200:
            return True
        com_logger.error(f"DELETE request failed for {endpoint}: {response.json()}")
        return False

    def close(self):
        """ 关闭连接 """
        com_logger.info("Opentrons Connection closed.")


if __name__ == '__main__':
    ot_connection = OpentronsConnection(mock=False)
    protocols = ot_connection.get("/protocols")
    if protocols:
        com_logger.info(f"Retrieved protocols: {protocols}")
    ot_connection.close()
