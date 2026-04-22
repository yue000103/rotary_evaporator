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
                if err_msg.startswith("❌ Timeout waiting for response:"):
                    if hasattr(self.connect, "is_connected") and not self.is_connected():
                        print("⚠️ Detected disconnection, attempting to reconnect...")
                        for _ in range(retry_count):
                            try:
                                self.connect()
                                print("✅ Reconnection successful")
                            except Exception as re:
                                print(f"Reconnection failed: {re}")
                                time.sleep(1)
                        print("❌ Failed to reconnect after 3 attempts, raising exception")
                        raise
                    print("Please select: 1. Continue (skip) 2. Retry 3. End experiment")
                    choice = input("Enter choice (1/2/3): ").strip()
                    if choice == "1":
                        print("⏭️ Skipping this method")
                        return False
                    elif choice == "2":
                        print("🔄 Retrying this method")
                        return func(self, cmd_full, *args, **kwargs)
                    else:
                        print("🛑 Ending experiment, raising exception")
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
        print("mock:", self.mock)

        if not self.mock:
            print("Connecting to ABB controller...")
            self.connect()

    def connect(self):
        while True:
            try:
                self.sock = socket.socket()
                self.sock.connect((self.ip, self.port))
                print(f"✅ Connected to ABB controller ({self.ip}:{self.port})")
                threading.Thread(target=self.recv_thread, daemon=True).start()
                return
            except Exception as e:
                print(f"❌ Robot connection failed: {e}, retrying...")
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
                print(f"⚠️ Receive thread error: {e}")
                for i in range(retry_count):
                    print(f"🔄 Attempt {i+1} to reconnect...")
                    try:
                        self.connect()
                        print("✅ Receive thread reconnection successful")
                        break
                    except Exception as re:
                        print(f"❌ Receive thread reconnection failed: {re}")
                        time.sleep(1)
                else:
                    print("❌ Receive thread failed to reconnect after 3 attempts, raising exception")
                    raise
            except Exception as e:
                print(f"⚠️ Receive thread other exception: {e}")
                raise

    @scenario_exception_handler
    def send_command(self, cmd):
        if self.mock:
            print(f"[MOCK] send: {cmd}")
            return
        print("cmd:", cmd)
        retry_count = 3
        for i in range(retry_count):
            try:
                self.sock.sendall((cmd + "\n").encode())
                print(f"✅ Command sent: {cmd}")
                return
            except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
                print(f"⚠️ Send command error: {e}")
                print(f"🔄 Attempt {i+1} to reconnect...")
                try:
                    self.connect()
                    print("✅ Send command reconnection successful")
                except Exception as re:
                    print(f"❌ Send command reconnection failed: {re}")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ Send command other exception: {e}")
                raise
        print("❌ Failed to reconnect after 3 attempts, raising exception")
        raise ConnectionError("Failed to send command after 3 reconnection attempts")

    def wait_for_response(self, expect, timeout_s=50):
        if self.mock:
            print(f"[MOCK] wait_for_response: {expect}")
            return
        timeout = time.time() + timeout_s
        while time.time() < timeout:
            with self.lock:
                if expect in self.recv_msg:
                    print(f"✅ Received acknowledgement: {expect}")
                    if expect != self.recv_msg:
                        logging.error('!!!!!!!!!!!!!!!! WRONG MESSAGE !!!!!!!!!!!!!!!!!!')
                        logging.error(f'Expected: {expect}, Received: {self.recv_msg}')
                    self.recv_msg = ''
                    return True
                elif self.recv_msg:
                    print(f"message: {self.recv_msg}")
            time.sleep(0.1)
        raise TimeoutError(f"❌ Timeout waiting for response: {expect}")

    def close(self):
        if self.sock:
            self.sock.close()
            print("✅ Robot connection closed")
        else:
            print("⚠️ Robot connection not initialized or already closed")

    def is_connected(self):
        try:
            if self.sock is None:
                return False
            self.sock.send(b'')
            return True
        except Exception:
            return False

    def __del__(self):
        self.close()