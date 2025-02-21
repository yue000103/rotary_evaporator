import socket
import time
import logging
from src.uilt.yaml_control.setup import get_base_url
from src.uilt.logs_control.setup import com_logger


class RobotConnection:
    def __init__(self,mock=False):
        """
        机器人通信控制
        :param host: 机器人服务器 IP
        :param port: 机器人服务器端口
        :param mock: 是否启用 Mock 模式
        """
        self.host = get_base_url("robot_com")
        self.port = 2000
        self.mock = mock
        self.sock = None

        if not self.mock:
            self._connect()

        com_logger.info(f"RobotConnection initialized on {self.host}:{self.port}")

    def _connect(self):
        """ 初始化 TCP 连接 """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        com_logger.info("Connected to Robot Server")

    def send_command(self, command):
        """ 发送指令到机器人并接收响应 """
        if self.mock:
            com_logger.info(f"[Mock Mode] Sent: {command}")
            return f"[Mock Response] {command} {time.strftime('%H:%M:%S', time.localtime())}"

        try:
            self.sock.sendall(command.encode("utf-8"))
            response = self.sock.recv(1024).decode("utf-8")
            com_logger.info(f"Received: {response}")
            return response
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return None

    def close(self):
        """ 关闭连接 """
        if self.sock:
            self.sock.close()
            com_logger.info("Robot Connection closed")
