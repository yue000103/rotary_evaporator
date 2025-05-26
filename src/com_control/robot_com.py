import socket
import time
import logging
from unittest import mock
import threading

from src.uilt.yaml_control.setup import get_base_url
from src.uilt.logs_control.setup import com_logger


class RobotConnection:
    def __init__(self, mock=False):
        """
        机器人通信控制
        :param mock: 是否启用 Mock 模式
        """
        self.host = '192.168.1.91'
        self.port = 2000  # 服务器端口号
        self.mock = mock
        self.server_socket = None
        self.client_address = None


        if mock is False:
            self._start_server()
        com_logger.info(f"RobotConnection initialized on {self.host}:{self.port}")

    def _start_server(self):
        """ 初始化 TCP 服务器 """
        max_retries = 2  # 最大重试次数
        retry_count = 0  # 当前重试计数

        while retry_count <= max_retries:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.host, self.port))
                print("robot_com: 成功链接")
                break  # 连接成功时退出循环
            except Exception as e:
                print("robot_com:", e)
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"连接失败，正在尝试第 {retry_count} 次重连...")
                else:
                    print("已达到最大重试次数，停止连接")
                    break  # 达到最大重试次数时退出循环



    def send_command(self, command):
        """ 发送指令到机器人并接收响应 """
        if self.mock:
            com_logger.info(f"[Mock Mode] Sent: {command}")
            print(f"command:{command}")
            time.sleep(1)
            return f"[Mock Response] {command} {time.strftime('%H:%M:%S', time.localtime())}"

        try:
            print("self.server_socket",self.server_socket)
            self.server_socket.sendall((command + "\n").encode())
            print("command；",command)
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return None

    def close(self):
        """ 关闭连接 """
        try:
            if self.server_socket:
                self.server_socket.close()
                com_logger.info("Client connection closed")

        except Exception as e:
            com_logger.error(f"Error closing connection: {e}")

    def wait_for_target(self, expected):
        print(f"⏳ 等待确认回复：{expected}")

        if self.mock:
            time.sleep(2)
            return "Sample"

        while True:
            try:
                reply = self.server_socket.recv(1024).decode().strip()
                print("📥 收到回复：", reply)
                if expected in reply:
                    print(f"✅ 收到确认：{expected}")
                    # input("🟢 已收到确认，按回车继续发送下一条...")
                    return expected
            except Exception as e:
                print(f"⚠ 接收出错：{e}")
                time.sleep(1)



if __name__ == "__main__":
    robot = RobotConnection()
    # while True:
    #     robot.accept_client()
    #
    #     robot.send_command('start')
