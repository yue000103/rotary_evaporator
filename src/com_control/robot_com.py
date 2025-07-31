import logging
import socket
import threading
import time
import functools

def scenario_exception_handler(func):
    @functools.wraps(func)
    def wrapper(self, cmd_full, *args, **kwargs):
        retry_count = 3
        while True:
            try:
                return func(self, cmd_full, *args, **kwargs)
            except TimeoutError as e:
                err_msg = str(e)
                # 只处理特定超时
                if err_msg == f"❌ 超时未收到":
                    # 检查是否断链
                    if hasattr(self.connect, "is_connected") and not self.is_connected():
                        print("⚠️ 检测到断链，正在尝试重连...")
                        for _ in range(retry_count):
                            try:
                                self.connect()
                                print("✅ 重连成功")
                            except Exception as re:
                                print(f"重连失败: {re}")
                                time.sleep(1)
                        print("❌ 重连3次失败，抛出异常")
                        raise
                    # 没断链，用户选择
                    print("请选择：1.继续（跳过此步） 2.重新执行 3.结束实验")
                    choice = input("输入选项（1/2/3）：").strip()
                    if choice == "1":
                        print("⏭️ 跳过此方法")
                        return False
                    elif choice == "2":
                        print("🔄 重新执行此方法")
                        return func(self, cmd_full, *args, **kwargs)
                    else:
                        print("🛑 结束实验，抛出异常")
                        raise
                else:
                    raise
    return wrapper



class RobotConnection:
    def __init__(self, ip="192.168.1.91", port=2000, mock=False):
        self.ip = ip
        self.port = port
        self.mock = mock
        self.sock = None
        self.recv_msg = ""
        self.lock = threading.Lock()
        print("self.mock",self.mock)

        if not self.mock:
            print("正在连接到 ABB 控制器...")
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
        retry_count = 3
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
            except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
                print(f"⚠️ 接收线程异常: {e}")
                for i in range(retry_count):
                    print(f"🔄 尝试第{i+1}次重连...")
                    try:
                        self.connect()
                        print("✅ 接收线程重连成功")
                        break
                    except Exception as re:
                        print(f"❌ 接收线程重连失败: {re}")
                        time.sleep(1)
                else:
                    print("❌ 接收线程重连3次失败，抛出异常")
                    raise
            except Exception as e:
                print(f"⚠️ 接收线程其他异常: {e}")
                raise

    @scenario_exception_handler
    def send_command(self, cmd):
        if self.mock:
            print(f"[MOCK] send: {cmd}")
            return
        print("cmd",cmd)
        retry_count = 3
        for i in range(retry_count):
            try:
                self.sock.sendall((cmd + "\n").encode())
                print(f"✅ 发送命令：{cmd}")
                return
            except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
                print(f"⚠️ 发送命令异常: {e}")
                print(f"🔄 尝试第{i+1}次重连...")
                try:
                    self.connect()
                    print("✅ 发送命令重连成功")
                except Exception as re:
                    print(f"❌ 发送命令重连失败: {re}")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ 发送命令其他异常: {e}")
                raise
        print("❌ 发送命令重连3次失败，抛出异常")
        raise ConnectionError("发送命令重连3次失败")

    def wait_for_response(self, expect, timeout_s=50):
        if self.mock:
            print(f"[MOCK] wait_for_response: {expect}")
            return
        timeout = time.time() + timeout_s
        while time.time() < timeout:
            with self.lock:
                if expect in self.recv_msg:
                    print(f"✅ 收到确认：{expect}")
                    if expect != self.recv_msg:
                        logging.error('!!!!!!!!!!!!!!!! WRONG MESSAGE !!!!!!!!!!!!!!!!!!')
                        logging.error(f'Expected: {expect}, Received: {self.recv_msg}')
                    self.recv_msg = ''
                    return True
                elif self.recv_msg:
                    print(f"message: {self.recv_msg}")
            time.sleep(0.1)
        raise TimeoutError(f"❌ 超时未收到：{expect}")

    def close(self):
        if self.sock:
            self.sock.close()
            print("✅ 机器人连接已关闭")
        else:
            print("⚠️ 机器人连接未初始化或已关闭")

    def is_connected(self):
        try:
            if self.sock is None:
                return False
            self.sock.send(b'')  # 发送空字节检测连接
            return True
        except Exception:
            return False


    def __del__(self):
        self.close()