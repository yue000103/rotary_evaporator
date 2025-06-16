import socket
import threading
import time


class RobotConnection:
    def __init__(self, ip="192.168.1.91", port=2000, mock=False):
        self.ip = ip
        self.port = port
        self.mock = mock
        self.sock = None
        self.recv_msg = ""
        self.lock = threading.Lock()

        if not self.mock:
            self.connect()

    def connect(self):
        while True:
            try:
                self.sock = socket.socket()
                self.sock.connect(("192.168.1.91", 2000))
                print(f"✅ 已连接到 ABB 控制器 ({self.ip}:{self.port})")
                threading.Thread(target=self.recv_thread, daemon=True).start()
                return
            except Exception as e:
                print(f"❌ 机械臂   连接失败：{e}，重试中...")
                time.sleep(2)

    def recv_thread(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024)
                if data:
                    buffer += data.decode()
                    if "\n" in buffer:
                        lines = buffer.split("\n")
                        buffer = lines[-1]
                        for line in lines[:-1]:
                            msg = line.strip()
                            if msg:
                                with self.lock:
                                    self.recv_msg = msg
                    else:
                        with self.lock:
                            self.recv_msg = data.decode()
            except:
                print("⚠️ 接收线程异常")
                break

    def send_command(self, cmd):
        if self.mock:
            print(f"[MOCK] send: {cmd}")
            return
        self.sock.sendall((cmd + "\n").encode())

    def wait_for_response(self, expect, timeout_s=10):
        if self.mock:
            print(f"[MOCK] wait_for_response: {expect}")
            return
        timeout = time.time() + timeout_s
        while time.time() < timeout:
            with self.lock:
                if self.recv_msg == expect:
                    print(f"✅ 收到确认：{expect}")
                    self.recv_msg = ''
                    return True
                elif self.recv_msg:
                    print(f"message: {self.recv_msg}")
            time.sleep(0.1)
        raise TimeoutError(f"❌ 超时未收到：{expect}")
