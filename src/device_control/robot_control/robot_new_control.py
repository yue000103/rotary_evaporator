import socket
import threading
import time

ip = '192.168.1.91'
port = 2000

command_list = [
    {"send": "task_scara_zhuzi1_py"},
    {"send": "task_scara_zhuzi2_py"},
    {"send": "task_scara_sample_py"},
    {"send": "task_scara_clean_py"},
    {"send": "task_flask_move_py"},
    {"send": "task_transfer_flask_liquid_py"},
    {"send": "task_Rotary_Evaporator_put_py"},
    {"send": "task_Rotary_Evaporator_get_py"},
    {"send": "task_shake_the_flask_py"},
    {"send": "task_abb_clean_py"},
    {"send": "task_scara_get_tool"},
    {"send": "task_scara_put_tool"},
    {"send": "task_scara_filling_liquid_ok"},
    {"send": "clean_ok"},
    {"send": "abb_clean_ok"},
    {"send": "sample_clean_finish"},
    {"send": "sample_ok"},
    {"send": "Vacuum reset"},
    {"send": "Vacuum_ok"},
    {"send": "Liquid_transfer_ok"},
    {"send": "start"},
]

sock = None
recv_msg = ""
lock = threading.Lock()

def connect():
    global sock
    while True:
        try:
            sock = socket.socket()
            sock.connect((ip, port))
            print(f"✅ 已连接到 ABB 控制器 ({ip}:{port})")
            threading.Thread(target=recv_thread, daemon=True).start()
            return
        except Exception as e:
            print(f"❌ 连接失败：{e}，重试中...")
            time.sleep(2)

def recv_thread():
    print('recv thread start')
    global recv_msg
    buffer = ""
    while True:
        try:
            data = sock.recv(1024)
            if data:
                print(f'{data=}')
                buffer += data.decode()
                if "\n" in buffer:
                    lines = buffer.split("\n")
                    buffer = lines[-1]
                    for line in lines[:-1]:
                        msg = line.strip()
                        if msg:
                            print(f"📥 接收：{msg}")
                            with lock:
                                recv_msg = bytes.decode(msg)
                else:
                    print(f"📥 接收：{data}")
                    with lock:
                        recv_msg = bytes.decode(data)
        except:
            print("⚠️ 接收线程异常")
            break

def wait_for_response(expect, timeout_s = 10):
    global recv_msg
    print(f'{expect} expected with timeout {timeout_s}s')
    timeout = time.time() + timeout_s
    while time.time() < timeout:
        with lock:
            if recv_msg == expect:
                print(f"✅ 已收到确认：{expect}")
                recv_msg = ''
                return True
            elif recv_msg:
                print(f'message: {recv_msg} received')

        time.sleep(0.1)
    print(f"❌ 超时未收到：{expect}")
    raise TimeoutError(f"❌ 超时未收到：{expect}")


def sync(command):
    wait_for_response(command+"_finish")

def check(command):
    wait_for_response(command+"ok")

def run():
    global recv_msg
    while True:
        try:
            print("\n📋 输入编号 或 编号+参数（如 1 abc），q退出")
            for i, item in enumerate(command_list):
                print(f"{i+1:>2}. {item['send']}")
            choice = input("🟢 指令：").strip()
            if choice == "q":
                break

            parts = choice.split(maxsplit=1)
            if not parts[0].isdigit():
                continue
            idx = int(parts[0]) - 1
            if idx < 0 or idx >= len(command_list):
                continue

            cmd = command_list[idx]["send"]
            if cmd.startswith("task_") and len(parts) == 2:
                cmd_full = f"{cmd}({parts[1]})"
            else:
                cmd_full = cmd

            with lock:
                recv_msg = ""

            sock.sendall((cmd_full + "\n").encode())
            print(f"📤 已发送：{cmd_full}")
            wait_for_response(cmd_full + "ok")
            wait_for_response(cmd_full + "_finish", 120)
        except Exception as e:
            print(f'Error! {e}')

connect()
# time.sleep(100)
run()
