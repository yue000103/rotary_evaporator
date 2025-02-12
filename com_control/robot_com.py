import socket
import time
from typing import Optional
from src.utils.logger import com_logger  # 确保正确导入 logger

class RobotCom:
    def __init__(self, host: str = '192.168.23.10', port: int = 2000, mock: bool = False) -> None:
        """
        初始化 RobotCom 实例

        :param host: 服务器绑定的地址，默认为 '192.168.23.10'
        :param port: 服务器绑定的端口，默认为 2000
        :param mock: 是否启用模拟模式，若为 True，则不实际连接
        """
        self.host = host
        self.port = port
        self.mock = mock
        self.server: Optional[socket.socket] = None
        self.is_running: bool = False

    def start_server(self) -> None:
        """
        启动服务器。如果 mock 为 True，则模拟服务器启动。
        """
        if self.mock:
            com_logger.info("Mock mode enabled. Server is not actually started.")
            return

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        self.is_running = True
        com_logger.info(f"Server started at {self.host}:{self.port}")

        try:
            while self.is_running:
                conn, addr = self.server.accept()
                com_logger.info(f"Connection established with {addr}")
                self.handle_client(conn)
        except KeyboardInterrupt:
            com_logger.warning("Server shutting down due to keyboard interrupt.")
        except Exception as e:
            com_logger.error(f"Unexpected error: {e}")
        finally:
            self.stop_server()

    def handle_client(self, conn: socket.socket) -> None:
        """
        处理客户端连接

        :param conn: 客户端 socket 对象
        """
        with conn:
            while self.is_running:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    received_message = data.decode()
                    com_logger.info(f"Received: {received_message}")

                    response = f"Hello from Python {time.strftime('%H:%M:%S', time.localtime())}"
                    conn.send(response.encode('utf-8'))
                    com_logger.info(f"Response sent: {response}")
                except Exception as e:
                    com_logger.error(f"Error during communication with client: {e}")
                    break

    def stop_server(self) -> None:
        """
        停止服务器，释放资源
        """
        self.is_running = False
        if self.server:
            self.server.close()
            com_logger.info("Server stopped.")

if __name__ == '__main__':
    robot_com = RobotCom(mock=True)
    robot_com.start_server()  # 不会实际连接，但会输出日志

