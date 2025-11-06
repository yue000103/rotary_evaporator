from src.com_control.PLC_com import PLCConnection
import threading
import time
import json
from src.util.logs_control.setup import device_control_logger

class RobotPLC:
    def __init__(self, mock=False):
        self.mock = mock
        self.plc = PLCConnection(mock=mock)
        self.robot_error = False
        self.busy_flag = 0
        self.start_flag = False
        self.finish_flag = True
        self.BUSY_FLAG_ADDRESS = 1111  # int
        self.FUN_NAME_ADDRESS = 1100  # int
        self.FUN_PARAMS_ADDRESS = 1101  # int
        self.FINISH_FLAG_ADDRESS = 1101  # bool
        self.START_FLAG_ADDRESS = 1002  # bool
        self.ROBOT_ERROR_ADDRESS = 1004  # bool

        # 读取 JSON 文件
        self.json_path = r"D:\back\rotary_evaporator\src\device_control\robot_control\robot_fun.json"
        # 读取 JSON 文件
        self.function_map = self.load_function_map(self.json_path)

        if self.mock is False:
            # 启动轮询线程
            self.polling_thread = threading.Thread(target=self.poll_plc_status, daemon=True)
            self.polling_thread.start()


    def poll_plc_status(self):
        """
        轮询 PLC 的状态信号:
        - robot_error (ROBOT_ERROR_ADDRESS)
        - busy_flag (BUSY_FLAG_ADDRESS)
        - finish_flag (FINISH_FLAG_ADDRESS)
        """
        while True:
            try:
                self.robot_error = self.plc.read_coils(self.ROBOT_ERROR_ADDRESS)
                self.busy_flag = self.plc.read_holding_registers(self.BUSY_FLAG_ADDRESS,1)
                self.finish_flag = self.plc.read_coils(self.FINISH_FLAG_ADDRESS)
            except Exception as e:
                print(f"轮询 PLC 状态失败: {e}")
                self.robot_error = False
                self.busy_flag = -1
                self.finish_flag = False
            time.sleep(1)  # 轮询间隔 1 秒



    def load_function_map(self, file_path):
        """加载 JSON 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 JSON 文件失败: {e}")
            return {}


    def reset_start_flag(self):
        """重置启动标志位"""
        self.plc.write_coil(self.START_FLAG_ADDRESS, False)

    def run_fun(self, fun_name: str, fun_params: dict):
        """
        运行机器人功能：
        - fun_name: 需要执行的功能名（如 "run_A_to_B"）
        - fun_params: 该功能需要的参数（如 {"p_A":20, "p_B":90}）
        """
        if fun_name not in self.function_map:
            print(f"错误: 未找到功能 {fun_name}")
            return False

        fun_data = self.function_map[fun_name]
        num = fun_data["num"]  # 获取功能编号
        param_map = fun_data["params"]  # 获取参数映射

        # 写入功能编号
        self.plc.write_single_register(self.FUN_NAME_ADDRESS, num)

        # 写入参数
        param_values = []
        for param_name, param_index in param_map.items():
            if param_name in fun_params:
                param_value = fun_params[param_name]
                param_address = self.FUN_PARAMS_ADDRESS + (param_index - 1)  # 计算参数存储地址
                self.plc.write_registers(param_address, param_value)
                param_values.append((param_address, param_value))
            else:
                print(f"警告: 缺少参数 {param_name}")

        # 启动机器人
        self.plc.write_coil(self.START_FLAG_ADDRESS, True)

        print(f"已启动功能 {fun_name} (编号 {num})，参数: {param_values}")

        self.function_running()
        print(f"正在运行 {fun_name} (编号 {num})，参数: {param_values}")

        self.plc.write_coil(self.START_FLAG_ADDRESS, False)

        self.function_finish()
        print(f"运行结束 {fun_name} (编号 {num})，参数: {param_values}")

        self.plc.write_coil(self.FINISH_FLAG_ADDRESS, False)


        return True

    def execute_function(self, fun_name: str, fun_params: dict):
        """
        执行机器人功能前检查BUSY_FLAG_ADDRESS是否为0
        - 如果BUSY_FLAG_ADDRESS不为0，则返回错误
        - 如果为0，则执行run_fun
        """
        while True:
            if self.busy_flag != 0:
                print(f"错误: 机器人正忙 (BUSY_FLAG_ADDRESS={self.busy_flag})，无法执行 {fun_name}")
            else:
                return self.run_fun(fun_name, fun_params)
            time.sleep(1)


    def function_running(self):
        """
        执行机器人功能前检查BUSY_FLAG_ADDRESS是否为0
        - 如果BUSY_FLAG_ADDRESS不为0，则返回错误
        - 如果为0，则执行run_fun
        """
        while True:
            if self.busy_flag == 1:
                print(f"机器人开始运行.........")
                return
            print("机器人还没有开始运行........")
            time.sleep(1)

    def function_finish(self):
        """
        执行机器人功能前检查BUSY_FLAG_ADDRESS是否为0
        - 如果BUSY_FLAG_ADDRESS不为0，则返回错误
        - 如果为0，则执行run_fun
        """
        while True:
            if self.finish_flag is True:
                print("机器人运行结束........")
                return
            print("机器人正在运行........")
            time.sleep(1)


if __name__ == '__main__':
    robot_plc = RobotPLC(True)
    fun_name = "run_A_to_B"
    fun_params = {
        "p_A":20,
        "p_B":30,
        "p_C":60
    }
    robot_plc.execute_function(fun_name,fun_params)


