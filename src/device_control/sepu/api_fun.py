import requests
import json
from datetime import datetime
import time
from src.com_control.sepu_com import SepuCom

class ApiClient:
    def __init__(self,):
        """
        初始化ApiClient实例，设置基本的API URL。

        参数:
        base_url (str): API的基本URL，例如 "http://localhost:5000"
        """
        self.sepu_com = SepuCom()
        self.method_id = 0



    def init_device(self, use_mock: bool) -> dict:
        """
        调用 /status/init_device 接口初始化设备状态。

        参数:
        use_mock (bool): 设置是否使用mock模式。

        返回:
        dict: 接口返回的响应数据
        """
        payload = {"use_mock": use_mock}
        return self.sepu_com.send_post_request("/status/init_device", payload)

    def get_device_status(self, status: str, type: str) -> dict:
        """
        调用 /status/get_device_status 接口获取设备状态。

        参数:
        status (str): 设备的状态（如 'active' 或 'inactive'）。
        type (str): 设备类型（如 'device' 或其他类型）。

        返回:
        dict: 接口返回的响应数据
        """
        payload = {
            "status": status,
            "type": type
        }
        return self.sepu_com.send_post_request("/status/get_device_status", payload)

    def update_method(self, method_id: str, method: dict) -> dict:
        """
        调用 /method/update/operate 更新方法。

        参数:
        method_id (str): 方法ID。
        method (dict): 包含方法更新的详细数据。

        返回:
        dict: 接口返回的响应数据
        """
        payload = {
            "method": method,
            "method_id": method_id
        }
        self.method_id = method_id
        return self.sepu_com.send_post_request("/method/update/operate", payload)

    def only_operate(self) -> dict:
        """
        调用 /method/only/operate 上传方法。

        返回:
        dict: 接口返回的响应数据
        """
        return self.sepu_com.send_get_request("/method/only/operate")

    def get_curve(self, start_time: str) -> dict:
        """
        调用 /eluent_curve/get_curve 开始实验。

        参数:
        start_time (str): 曲线开始时间

        返回:
        dict: 接口返回的响应数据
        """
        payload = {
            "start_time": start_time
        }
        return self.sepu_com.send_post_request("/eluent_curve/get_curve", payload)

    def update_line_pause(self) -> dict:
        """
        调用 /eluent_curve/update_line_pause 暂停实验。

        返回:
        dict: 接口返回的响应数据
        """
        return self.sepu_com.send_get_request("/eluent_curve/update_line_pause")

    def update_line_terminate(self) -> dict:
        """
        调用 /eluent_curve/update_line_terminate 终止实验。

        返回:
        dict: 接口返回的响应数据
        """
        return self.sepu_com.send_get_request("/eluent_curve/update_line_terminate")

    def save_experiment_data(self) -> dict:
        """
        调用 /experiment/save/experiment_data 保存实验数据。

        参数:
        curve_data (list): 曲线数据，包含多个曲线点。
        experiment_id (int): 实验ID。
        method_id (int): 方法ID。
        sampling_time (int): 采样时间。
        task_list (list): 任务列表。
        vertical_data (list): 垂直数据。

        返回:
        dict: 接口返回的响应数据
        """
        payload={}
        # payload = {
        #     "curve_data": curve_data,
        #     "experiment_id": experiment_id,
        #     "method_id": method_id,
        #     "sampling_time": sampling_time,
        #     "task_list": task_list,
        #     "vertical_data": vertical_data
        # }
        return self.sepu_com.send_post_request("/experiment/save/experiment_data",payload)

    def get_line(self) -> dict:
        """
        调用 /eluent_curve/get_line 接口获取流动相曲线数据。

        返回:
        dict: 接口返回的响应数据
        """
        return self.sepu_com.send_get_request("/eluent_curve/get_line")

    def get_current_time(self):
        """
        获取当前时间，格式为 YYYY-MM-DD HH:MM:SS
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_tube(self, task_list:dict) -> dict:
        """
        调用 /tubes/get_tube 接口获取指定的管路任务信息。

        参数:
        task_list (list): 任务列表，包含多个任务对象，每个对象需要包含：
                          - method_id (int): 方法ID
                          - module_id (int): 模块ID
                          - status (str): 任务状态 abandon、collect、clean
                          - task_id (int): 任务ID
                          - tube_list (list): 试管ID列表

        返回:
        dict: 接口返回的响应数据
        """
        payload = {
            "task_list": task_list
        }
        print("payload",payload)
        return self.sepu_com.send_post_request("/tubes/get_tube", payload)

    def get_tube_status(self):
        '''
        ture: 表示执行结束
        false：表示还有任务在执行
        :return:
        '''
        return self.sepu_com.send_get_request("/tubes/get_tube_status")

    def pause_tube(self) -> dict:
        """
        调用 /tubes/pause_tube 接口暂停管路任务。

        返回:
        dict: 接口返回的响应数据
        """
        return self.sepu_com.send_post_request("/tubes/pause_tube", {})

    def resume_tube(self) -> dict:
        """
        调用 /tubes/resume_tube 接口恢复管路任务。

        返回:
        dict: 接口返回的响应数据
        """
        return self.sepu_com.send_post_request("/tubes/resume_tube", {})

    def set_sample_valve(self) -> dict:
        """
        调用 /eluent_curve/set_sample_valve 。

        参数:
        valve_position (int): 进样阀的位置。

        返回:
        dict: 接口返回的响应数据
        """
        payload = {

        }
        return self.sepu_com.send_post_request("/eluent_curve/set_sample_valve", payload)

    def update_line_start(self):
        return self.sepu_com.send_get_request("/eluent_curve/update_line_start")

    # def pause_expriment(self):
    #     return self.sepu_com.send_get_request("/eluent_curve//update_line_pause")


    def set_start_tube(self,tube_id,module_id)-> dict:
        payload = {
            "detector_zeroing": True,
            "pump_pressure_zeroing":True,
            "tube_id":tube_id,
            "module_id":module_id,
        }
        return self.sepu_com.send_post_request("/eluent_curve/init", payload)


def main():
    # 创建 ApiClient 实例
    api_client = ApiClient()

    while True:
        print("\n请选择要执行的操作（输入数字）：")
        print("1. 初始化设备")
        print("2. 更新方法")
        print("3. 上传方法")
        print("4. 获取Line")
        print("5. 开始实验")
        print("11. 上样结束")


        print("6. 终止实验")
        print("7. 保存实验数据")
        print("8. 收集试管")
        print("9. 暂停试管收集")
        print("10. 继续试管收集")
        print("0. 退出")

        choice = input("请输入你的选择: ").strip()

        if choice == "0":
            print("退出程序")
            break

        elif choice == "1":
            # 设备初始化
            result = api_client.init_device(True)
            print("Init Device Result:")

        elif choice == "2":
            # 更新方法
            method = {
                "samplingTime": 5,
                "detectorWavelength": 258,
                "equilibrationColumn": 1,
                "speed": 100,
                "totalFlowRate": 10,
                "cleanList": [
                    {
                        "module_id": 2,
                        "liquid_volume": 20,
                        "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    },
                    {
                        "module_id": 1,
                        "liquid_volume": 20,
                        "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    }
                ],
                "cleaningCount": 2,
                "cleaningSpeed": None,
                "drainSpeed": None,
                "isocratic": 0,
                "methodName": "12",
                "pressure": 1,
                "pumpA": None,
                "pumpB": None,
                "pumpList": [
                    {"time": 0, "pumpB": 100, "pumpA": 0, "flowRate": 30},
                    {"time": 1, "pumpB": 100, "pumpA": 0, "flowRate": 30},
                    {"time": 2, "pumpB": 0, "pumpA": 100, "flowRate": 30},
                    {"time": 3, "pumpB": 0, "pumpA": 100, "flowRate": 30},
                    {"time": 4, "pumpB": 0, "pumpA": 100, "flowRate": 30},
                    {'time': 5, "pumpB": 0, "pumpA": 100, "flowRate": 30},
                ],
                "retainList": [
                    {
                        "module_id": 1,
                        "liquid_volume": 8,
                        "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    },
                    {
                        "module_id": 2,
                        "liquid_volume": 8,
                        "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    }
                ],
                "smiles": "4896",
            }
            method_id = "97"

            result = api_client.update_method(method_id, method)
            print("Update Method Result:")

        elif choice == "3":
            # 仅执行操作
            result = api_client.only_operate()
            print("Only Operate Result:")

        elif choice == "4":
            # 获取 Line 数据
            result = api_client.get_line()
            print("Get Line Result:")

        elif choice == "5":
            # 开始实验
            start_time = api_client.get_current_time()
            result = api_client.get_curve(start_time)
            print("Get Curve Result:")

        elif choice == "6":
            # 终止实验
            result = api_client.update_line_terminate()
            print("Update Line Terminate Result:")

        elif choice == "7":
            # 保存实验数据
            result = api_client.save_experiment_data()
            print("Save Experiment Data Result:")
        elif choice == "8":
            timestamp = time.strftime("%Y%m%d%H%M%S")
            task_list = {
                    "method_id": int(api_client.method_id),
                    "module_id": 1,
                    "status": "abandon",
                    "task_id": int(timestamp),
                    "tube_list": [1, 2, 3, 4]
                }

            print("task_list",task_list)

            # 调用 /tubes/get_tube 接口
            result = api_client.get_tube(task_list)
            print("Get Tube Result:")
            print(json.dumps(result, indent=2))
        elif choice == "9":
            result = api_client.pause_tube()
            print("Pause Tube Result:")
            print(json.dumps(result, indent=2))
        elif choice == "10":
            result = api_client.resume_tube()
            print("Resume Tube Result:")
            print(json.dumps(result, indent=2))
        elif choice == "11":
            result = api_client.set_sample_valve()
            print("Set Sample Valve Result:")
            print(json.dumps(result, indent=2))
        else:
            print("无效输入，请重新选择！")
            continue


        # 打印 JSON 结果
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
