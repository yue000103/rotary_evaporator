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
        self.sepu_api = ApiClient()


    def get_elution_curve(self):
        """ 调用交互窗口获取洗脱曲线数据 """
        app = QApplication.instance()  # 获取现有 QApplication 实例
        if not app:
            app = QApplication(sys.argv)  # 创建 QApplication 实例（避免重复）

        dialog = ExperimentDialog()
        if dialog.exec_() == QDialog.Accepted:  # 仅在用户点击确认后返回数据
            self.elution_curve = dialog.elution_curve

        return []  # 若未确认，返回空列表

    def write_params(self):
        # 读取 JSON 文件
        file_path = r"D:\back\rotary_evaporator\src\service_control\params.json"  # 确保路径正确
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # 更新 pumpList
        if "method" in data:
            data["method"]["pumpList"] = self.elution_curve
        else:
            print("Error: 'method' key not found in JSON file.")

        # 写回 JSON 文件
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("更新后的 pumpList 已成功写入 params.json")

    def get_experiment_data(self):
        result = self.sepu_api.save_experiment_data()
        print(result)


    def select_retain_tubes(self):
        """ 打开 PlotWithInputs 窗口，获取 tube_entries """
        self.get_experiment_data()
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        window = PlotWithInputs(self.curve_data, self.vertical_data, self.sampling_time)
        window.show()

        # **执行事件循环，直到窗口关闭**
        app.exec_()

        # **窗口关闭后，获取 tube_entries**
        tube = window.return_tube()

        def execute_task():
            timestamp = time.strftime("%Y%m%d%H%M%S")

            task_list = {
                "method_id": int(self.sepu_api.method_id),
                "module_id": module_id,  # 由用户输入
                "status": "retain",
                "task_id": int(timestamp),
                "tube_list": tube_list,  # 由用户输入
            }

            print("任务列表:", task_list)
            result = self.sepu_api.get_tube(task_list)
            print("获取试管结果:")
            print(json.dumps(result, indent=2))

        threading_cut = threading.Thread(target=execute_task)
        threading_cut.start()
        print("-------- 选中的 tubes --------", tube)


if __name__ == '__main__':
    sepu = SepuService()
    sepu.select_retain_tubes()