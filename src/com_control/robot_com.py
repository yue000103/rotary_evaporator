import socket
import time
import logging
from unittest import mock

from src.uilt.yaml_control.setup import get_base_url
from src.uilt.logs_control.setup import com_logger


class RobotConnection:
    def __init__(self, mock=False):
        """
        机器人通信控制
        :param mock: 是否启用 Mock 模式
        """
        self.host = '192.168.1.91'
        self.port = 1024  # 服务器端口号
        self.mock = mock
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        if mock is False:
            self._start_server()
        com_logger.info(f"RobotConnection initialized on {self.host}:{self.port}")

    def _start_server(self):
        """ 初始化 TCP 服务器 """
        # self.client_socket = socket.socket()
        # self.client_socket.connect((self.host,self.port))  # 绑定要监听的端口
        # print("self.host",self.host)
        # print("self.port",self.port)
        # print("self.server_socket",self.server_socket)
        # com_logger.info(f"Server started at {self.host}:{self.port}, waiting for connection...")
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = ('192.168.1.91', 1024)
            self.client_socket.connect(server_address)
            print("成功链接")
        except Exception as e:
            print("robot_com",e)

    def accept_client(self):
        """ 等待客户端连接 """
        if self.mock is True:
            print("is mock")
        try:

            self.client_socket, self.client_address = self.server_socket.accept()

            com_logger.info(f"Client connected from {self.client_address}")
        except Exception as e:

            com_logger.error(f"Client connection error: {e}")


    def send_command(self, command):
        """ 发送指令到机器人并接收响应 """
        if self.mock:
            com_logger.info(f"[Mock Mode] Sent: {command}")
            return f"[Mock Response] {command} {time.strftime('%H:%M:%S', time.localtime())}"

        try:
            print("self.client_socket",self.client_socket)
            self.client_socket.sendall(command.encode("utf-8"))
            print("command；",command)
            # response = self.client_socket.recv(1024).decode("utf-8")
            # response = self.client_socket.recv(1024)
            # print("response: ",response)

            # com_logger.info(f"Received: {response}")
            # return response

        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return None

    def close(self):
        """ 关闭连接 """
        try:
            if self.client_socket:
                self.client_socket.close()
                com_logger.info("Client connection closed")

        except Exception as e:
            com_logger.error(f"Error closing connection: {e}")



if __name__ == "__main__":
    robot = RobotConnection()
    # while True:
    #     robot.accept_client()
    #
    #     robot.send_command('start')
