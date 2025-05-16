import socket
import time

ip = '192.168.1.91'
port = 2000

# 每一条命令及其期待确认内容
data_dict = [
    {"send": "", "expect": "Sample loading ready"},  # 第1条手动输入
    {"send": "sample_ok", "expect": "clean ready"},
    {"send": "clean_ok", "expect": "ABB Reached Rotary Evaporator"},
    {"send": "Vacuum_ok", "expect": "wait_pc"},
    {"send": "Rotary evaporation completed", "expect": "wait_pc"},
    {"send": "Vacuum reset", "expect": "clean ready"},
    {"send": "clean_ok", "expect": "wait_pc"},
    {"send": "2", "expect": "Liquid transfer ready"},
    {"send": "Liquid transfer ok", "expect": "clean ready"},
    {"send": "clean ok", "expect": "Liquid transfer ready"},
    {"send": "Liquid transfer ok", "expect": "clean ready"},
    {"send": "clean ok", "expect": "Liquid transfer ready"},
    {"send": "Liquid transfer ok","expect":"Reached Rotary Evaporator"},
    {"send": "Vacuum_ok", "expect": "wait_pc"},
    {"send": "Rotary evaporation completed", "expect": "wait_pc"},
    {"send": "Vacuum reset", "expect": "finish"},
]

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((ip, port))
            print("✅ 已连接到 ABB")
            return s
        except:
            print("❌ 连接失败，2 秒后重试...")
            time.sleep(2)

def wait_for_target(sock, expected):
    print(f"⏳ 等待确认回复：{expected}")
    while True:
        try:
            reply = sock.recv(1024).decode().strip()
            print("📥 收到回复：", reply)
            if expected in reply:
                print(f"✅ 收到确认：{expected}")
                input("🟢 已收到确认，按回车继续发送下一条...")
                break
        except Exception as e:
            print(f"⚠ 接收出错：{e}")
            time.sleep(1)

def send_all(sock):
    for i, item in enumerate(data_dict):
        input(f"\n🟢 回车发送第 {i+1} 条：")
        # 第一条是用户输入
        if i == 0:
            msg = input("请输入第1条内容：").strip()
        else:
            msg = item["send"]
        sock.sendall((msg + "\n").encode())
        print("📤 已发送：", msg)
        wait_for_target(sock, item["expect"


execution_flow = [
        controller.await_sample_loading_ready,
        controller.trigger_clean_sequence,
        controller.proceed_to_evaporation_stage,
        controller.confirm_vacuum_prepared,
        controller.finalize_rotation_process,
        controller.reset_vacuum_system,
        controller.ready_clean,
        controller.input_numeric_command_2,
        controller.complete_transfer_process,
        controller.initiate_liquid_transfer,
        controller.ready_liquid_transfer,
        controller.confirm_vacuum_prepared,
        controller.finalize_rotation_process,
        controller.finalize_last
    ]