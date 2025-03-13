import requests
import json


class ApiClient:
    def __init__(self, base_url: str):
        """
        初始化ApiClient实例，设置基本的API URL。

        参数:
        base_url (str): API的基本URL，例如 "http://localhost:5000"
        """
        self.base_url = base_url

    def _send_post_request(self, endpoint: str, payload: dict) -> dict:
        """
        发送POST请求到指定的API接口。

        参数:
        endpoint (str): API的具体路径，如 "/status/init_device"
        payload (dict): 请求负载，作为JSON传递

        返回:
        dict: 请求的响应数据
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload)

        # 检查请求是否成功
        if response.status_code == 200:
            return response.json()  # 返回响应的JSON数据
        else:
            error_message = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            try:
                error_response = response.json()
                error_message["detailed_error"] = json.dumps(error_response, indent=2)
            except ValueError:
                error_message["detailed_error"] = "无法解析错误响应的JSON内容。"
            return error_message

    def _send_get_request(self, endpoint: str) -> dict:
        """
        发送GET请求到指定的API接口。

        参数:
        endpoint (str): API的具体路径，如 "/method/only/operate"

        返回:
        dict: 请求的响应数据
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            return response.json()  # 返回响应的JSON数据
        else:
            error_message = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            try:
                error_response = response.json()
                error_message["detailed_error"] = json.dumps(error_response, indent=2)
            except ValueError:
                error_message["detailed_error"] = "无法解析错误响应的JSON内容。"
            return error_message

    def init_device(self, use_mock: bool) -> dict:
        """
        调用 /status/init_device 接口初始化设备状态。

        参数:
        use_mock (bool): 设置是否使用mock模式。

        返回:
        dict: 接口返回的响应数据
        """
        payload = {"use_mock": use_mock}
        return self._send_post_request("/status/init_device", payload)

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
        return self._send_post_request("/status/get_device_status", payload)

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
        return self._send_post_request("/method/update/operate", payload)

    def only_operate(self) -> dict:
        """
        调用 /method/only/operate 上传方法。

        返回:
        dict: 接口返回的响应数据
        """
        return self._send_get_request("/method/only/operate")

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
        return self._send_post_request("/eluent_curve/get_curve", payload)

    def update_line_pause(self) -> dict:
        """
        调用 /eluent_curve/update_line_pause 暂停实验。

        返回:
        dict: 接口返回的响应数据
        """
        return self._send_get_request("/eluent_curve/update_line_pause")

    def update_line_terminate(self) -> dict:
        """
        调用 /eluent_curve/update_line_terminate 终止实验。

        返回:
        dict: 接口返回的响应数据
        """
        return self._send_get_request("/eluent_curve/update_line_terminate")

    def save_experiment_data(self, curve_data: list, experiment_id: int, method_id: int, sampling_time: int, task_list: list, vertical_data: list) -> dict:
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
        payload = {
            "curve_data": curve_data,
            "experiment_id": experiment_id,
            "method_id": method_id,
            "sampling_time": sampling_time,
            "task_list": task_list,
            "vertical_data": vertical_data
        }
        return self._send_post_request("/experiment/save/experiment_data", payload)





# 示例调用
if __name__ == "__main__":
    # 创建ApiClient实例，传入基本URL
    api_client = ApiClient("http://localhost:5000")

    # 获取设备初始化状态
    # result = api_client.init_device(True)
    # print(json.dumps(result, indent=2))

    # 获取设备状态
    # result = api_client.get_device_status("active", "device")
    # print(json.dumps(result, indent=2))

    # 更新方法
    method_payload = {
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
            {"time": 5, "pumpB": 0, "pumpA": 100, "flowRate": 30},
        ],
        "retainList": [
            {
                "module_id": 1,
                "liquid_volume": 8,
                "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        ],
        "smiles": "4896",
    }

    # result = api_client.update_method("97", method_payload)
    # print("Update Method Result:")
    # print(json.dumps(result, indent=2))

    # 调用 /method/only/operate 接口
    # 调用 /method/only/operate 接口
    # result = api_client.only_operate()
    # print("Only Operate Result:")
    # print(json.dumps(result, indent=2))

    # 调用 /eluent_curve/get_curve 接口
    start_time = "2025-03-13 15:01:20"
    # result = api_client.get_curve(start_time)
    # print("Get Curve Result:")
    # print(json.dumps(result, indent=2))

    # 构造实验数据
    curve_data = [{"time": "0:00:00", "value": 10}, {"time": "0:00:01", "value": 15}, {"time": "0:00:01", "value": 15} ,{"time": "0:00:01", "value": 15} ,{"time": "0:00:01", "value": 15}]
    experiment_id = 123
    method_id = 45
    sampling_time = 5
    task_list = []
    vertical_data = [{"time_start": "00:00:00", "time_end": "0:00:02", "module_index":0,"tube_index": 0},
                     {"time_start": "00:00:02", "time_end": "0:00:05", "module_index":0,"tube_index": 1},
                     {"time_start": "00:00:05", "time_end": "0:00:08", "module_index":0,"tube_index": 2},
                     {"time_start": "00:00:08", "time_end": "0:00:09", "module_index":0,"tube_index": 3}]

    # 调用 /experiment/save/experiment_data 接口
    result = api_client.save_experiment_data(curve_data, experiment_id, method_id, sampling_time, task_list,
                                             vertical_data)
    print("Save Experiment Data Result:")
    print(json.dumps(result, indent=2))
