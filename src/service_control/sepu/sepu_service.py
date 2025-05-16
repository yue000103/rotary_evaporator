import json
import sys

from datetime import datetime
import time
import threading

from PIL.ImagePalette import sepia

from src.uilt.logs_control.setup import service_control_logger
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (
    QApplication, QDialog
)
from src.service_control.sepu.experiment_graph import ExperimentDialog
from src.service_control.sepu.curve_graph import PlotWithInputs
from src.device_control.sepu.api_fun import ApiClient



class SepuService:
    def __init__(self):
        self.elution_curve = [
                {"time": 0, "pumpB": 100, "pumpA": 0, "flowRate": 20},
                {"time": 1, "pumpB": 100, "pumpA": 0, "flowRate": 20},
                {"time": 2, "pumpB": 0, "pumpA": 100, "flowRate": 20},
                {"time": 3, "pumpB": 0, "pumpA": 100, "flowRate": 20},
                {"time": 4, "pumpB": 0, "pumpA": 100, "flowRate": 20},
                {"time": 5, "pumpB": 0, "pumpA": 100, "flowRate": 20}
            ]
        self.retain_tube_list = []
        self.clean_tube_list = []
        self.curve_data = [
        {"time": "0:00:00", "value": 0.00126}, {"time": "0:00:01", "value": -0.00059},
        {"time": "0:00:02", "value": 0.01536}, {"time": "0:00:03", "value": 0.04066},
        {"time": "0:00:04", "value": 0.03933}, {"time": "0:00:05", "value": 0.0325},
        {"time": "0:00:06", "value": 0.04187}, {"time": "0:00:07", "value": 0.0463},
        {"time": "0:00:08", "value": 0.04318}, {"time": "0:00:09", "value": 0.03885},
        {"time": "0:00:10", "value": 0.03691}, {"time": "0:00:11", "value": 0.04046}
    ]
        self.vertical_data =  [
        {"time_start": "00:00:00", "time_end": "0:00:10", "tube": 1.0},
        {"time_start": "0:00:10", "time_end": "0:00:17", "tube": 2.0},
        {"time_start": "0:00:17", "time_end": "0:00:27", "tube": 3.0},
        {"time_start": "0:00:27", "time_end": "0:00:36", "tube": 4.0},
        {"time_start": "0:00:36", "time_end": "0:00:45", "tube": 5.0},
        {"time_start": "0:00:45", "time_end": "0:01:45", "tube": 6.0}

    ]
        self.sampling_time = 20
        self.total_flow_rate = 20
        self.sepu_api = ApiClient()
        self.method_id = '97'


    def get_elution_curve(self):
        """ 调用交互窗口获取洗脱曲线数据 """
        app = QApplication.instance()  # 获取现有 QApplication 实例
        if not app:
            app = QApplication(sys.argv)  # 创建 QApplication 实例（避免重复）

        dialog = ExperimentDialog()
        if dialog.exec_() == QDialog.Accepted:  # 仅在用户点击确认后返回数据
            self.elution_curve = dialog.elution_curve
            self.sampling_time = dialog.sampling_time
            self.total_flow_rate = dialog.total_flow_rate

        return []  # 若未确认，返回空列表

    def write_params(self):
        # 读取 JSON 文件
        file_path = r'D:\project_python\rotary_evaporator\src\service_control\params.json'
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # 更新 pumpList
        if "method" in data:
            data["method"]["pumpList"] = self.elution_curve
            data["method"]["totalFlowRate"] = self.total_flow_rate
            data["method"]["samplingTime"] = self.sampling_time
        else:
            print("Error: 'method' key not found in JSON file.")

        # 写回 JSON 文件
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("更新后的 pumpList 已成功写入 params.json")

    def get_experiment_data(self):
        result = self.sepu_api.save_experiment_data()
        self.vertical_data = result["vertical_data"]
        self.curve_data = result["curve_data"]

        print(result)

    def select_retain_tubes(self):
        """ 打开 PlotWithInputs 窗口，获取 tube_entries """

        try:
            self.get_experiment_data()
            print("self.curve_data",self.curve_data)
            print("self.vertical_data",self.vertical_data)
            print("self.sampling_time",self.sampling_time)

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            window = PlotWithInputs(self.curve_data, self.vertical_data, self.sampling_time)
            window.show()

            # 执行事件循环，直到窗口关闭
            app.exec_()

            # 窗口关闭后，获取 tube_entries
            tube = window.return_tube()
            # [{'module_id': 1, 'tube_list': [2, 3, 4]}, {'module_id': 2, 'tube_list': [4, 5, 6]}]

            print("tube",tube)
            self.retain_tube_list = tube
            self.find_clean_tubes()


            for tube_info in tube:
                timestamp = time.strftime("%Y%m%d%H%M%S")
                module_id = tube_info.get('module_id')
                tube_list = tube_info.get('tube_list')

                task_list = {
                    "method_id": int(self.sepu_api.method_id),
                    "module_id": int(module_id),  # 假设从 sepu_api 获取 module_id
                    "status": "retain",
                    "task_id": int(timestamp),
                    "tube_list": tube_list
                }

                print("任务列表:", task_list)
                result = self.sepu_api.get_tube(task_list)
                print("获取试管结果:")
                print(json.dumps(result, indent=2))
                time.sleep(1)

            return tube
        except Exception as e:
            print(f"发生错误: {e}")


    def find_clean_tubes(self):
        # 参数配置
        file_path = r'D:\project_python\rotary_evaporator\src\service_control\params.json'

        # 加载 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        retain_list = data.get("method", {}).get("retainList", [])

        # 构造 module_id -> 排除 tube_list 的字典
        exclude_dict = {item['module_id']: set(item['tube_list']) for item in self.retain_tube_list}

        # 处理 retainList，排除指定 tube
        result = []
        for retain in retain_list:
            module_id = retain['module_id']
            original_tubes = set(retain['tube_id'])
            exclude_tubes = exclude_dict.get(module_id, set())
            remaining_tubes = sorted(original_tubes - exclude_tubes)
            result.append({
                'module_id': module_id,
                'tube_list': remaining_tubes
            })
        self.clean_tube_list = result
        # 输出结果
        print(json.dumps(result, indent=4, ensure_ascii=False))

    def excute_clean_tubes(self):
        for tube_info in self.clean_tube_list:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            module_id = tube_info.get('module_id')
            tube_list = tube_info.get('tube_list')

            task_list = {
                "method_id": int(self.sepu_api.method_id),
                "module_id": int(module_id),  # 假设从 sepu_api 获取 module_id
                "status": "retain",
                "task_id": int(timestamp),
                "tube_list": tube_list
            }

            print("任务列表:", task_list)
            result = self.sepu_api.get_tube(task_list)
            print("获取试管结果:")
            print(json.dumps(result, indent=2))
            time.sleep(1)

        print("-------- 清洗的 tubes --------", self.clean_tube_list)


    def wash_column(self):
        self.get_elution_curve()
        self.write_params()

        # 参数配置
        file_path = r'D:\project_python\rotary_evaporator\src\service_control\params.json'

        # 加载 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            method = json.load(f)
        print(method["method"])
        result = self.sepu_api.update_method(self.method_id, method["method"])
        print("Update Method Result:", result)

        result = self.sepu_api.only_operate()
        print("Only Operate Result:", result)

        result = self.sepu_api.get_line()
        print("Get Line Result:", result)
        start_time = self.sepu_api.get_current_time()
        result = self.sepu_api.get_curve(start_time)
        return result



if __name__ == '__main__':
    sepu = SepuService()
    sepu.select_retain_tubes()