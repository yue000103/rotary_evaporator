import json
import sys

from datetime import datetime
import time
import ast

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
        service_control_logger.info('开始执行 __init__ 函数')

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

        service_control_logger.info('结束执行 __init__ 函数')

    def get_elution_curve(self):

        service_control_logger.info('开始执行 get_elution_curve 函数')

        """ 调用交互窗口获取洗脱曲线数据 """
        app = QApplication.instance()  # 获取现有 QApplication 实例
        if not app:
            app = QApplication(sys.argv)  # 创建 QApplication 实例（避免重复）

        dialog = ExperimentDialog()
        if dialog.exec_() == QDialog.Accepted:  # 仅在用户点击确认后返回数据
            self.elution_curve = dialog.elution_curve
            self.sampling_time = dialog.sampling_time
            self.total_flow_rate = dialog.total_flow_rate

        service_control_logger.info('结束执行 get_elution_curve 函数')


        return []  # 若未确认，返回空列表

    def write_params(self):
        service_control_logger.info('开始执行 write_params 函数')

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

        service_control_logger.info('结束执行 write_params 函数')

    def get_experiment_data(self):
        service_control_logger.info('开始执行 get_experiment_data 函数')

        result = self.sepu_api.save_experiment_data()
        self.vertical_data = result["vertical_data"]
        self.curve_data = result["curve_data"]

        print(result)

        service_control_logger.info('结束执行 get_experiment_data 函数')

    def select_retain_tubes(self,peak_id):
        service_control_logger.info('开始执行 select_retain_tubes 函数')

        """ 打开 PlotWithInputs 窗口，获取 tube_entries """

        # self.get_experiment_data()
        # print("self.curve_data",self.curve_data)
        # print("self.vertical_data",self.vertical_data)
        # print("self.sampling_time",self.sampling_time)
        #
        # app = QApplication.instance()
        # if app is None:
        #     app = QApplication(sys.argv)
        #
        # window = PlotWithInputs(self.curve_data, self.vertical_data, self.sampling_time)
        # window.show()
        #
        # # 执行事件循环，直到窗口关闭
        # app.exec_()
        #
        # # 窗口关闭后，获取 tube_entries
        # tube = window.return_tube()
        # tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}, {'module_id': 2, 'tube_list': [4, 5, 6,7,8,9,10]}]
        # tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}]
        retain_tube = self.sepu_api.get_task_list_by_peak_width(peak_id)
        print("select_retain_tubes 函数开始执行",retain_tube)
        tube = retain_tube["retain_tubes"]
        # while True:
        #     try:
        #         tube_input = input(
        #             "请输入峰数据（如：[{'module_id': 1, 'tube_list': [2, 3, 4]}, {'module_id': 2, 'tube_list': [4, 5, 6, 7, 8, 9, 10]}]）：")
        #         tube = ast.literal_eval(tube_input)
        #         print("你输入的tube数据：", tube)
        #
        #         if input("按Enter键继续收集峰数据..., 输入 exit 重新输入") == 'exit':
        #             continue
        #         break
        #     except Exception as e:
        #         print("输入错误，请重新输入正确的格式！")


        if len(tube) == 0:
            return 600
        # self.sepu_api.get_module_dict(tube)
        # self.retain_tube_list = tube
        # self.find_clean_tubes()


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
            time.sleep(10)

        while True:
            result = self.sepu_api.get_tube_status()
            print(f"收集液体:",result)
            if result["status"] == True:
                return 0
            time.sleep(2)

    def select_retain_tubes_by_id(self, peak_id):
        service_control_logger.info('开始执行 select_retain_tubes 函数')

        """ 打开 PlotWithInputs 窗口，获取 tube_entries """

        # self.get_experiment_data()
        # print("self.curve_data",self.curve_data)
        # print("self.vertical_data",self.vertical_data)
        # print("self.sampling_time",self.sampling_time)
        #
        # app = QApplication.instance()
        # if app is None:
        #     app = QApplication(sys.argv)
        #
        # window = PlotWithInputs(self.curve_data, self.vertical_data, self.sampling_time)
        # window.show()
        #
        # # 执行事件循环，直到窗口关闭
        # app.exec_()
        #
        # # 窗口关闭后，获取 tube_entries
        # tube = window.return_tube()
        # tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}, {'module_id': 2, 'tube_list': [4, 5, 6,7,8,9,10]}]
        # tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}]
        retain_tube = self.sepu_api.get_task_list_by_peak_id(peak_id)
        print("select_retain_tubes 函数开始执行", retain_tube)
        tube = retain_tube["retain_tubes"]
        print("tube", tube)
        if len(tube) == 0:
            return 600
        self.retain_tube_list = tube
        # self.find_clean_tubes()

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
            time.sleep(10)

        while True:
            result = self.sepu_api.get_tube_status()
            print(f"收集液体:", result)
            if result["status"] == True:
                return 0
            time.sleep(2)

    def get_peaks_num(self):
        peak = self.sepu_api.get_peaks_num()
        peaks_num = int(peak.get("peaks_num"))
        if not peaks_num:
            return 0
        return peaks_num

    def find_clean_tubes(self):

        service_control_logger.info('开始执行 find_clean_tubes 函数')

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

        service_control_logger.info('结束执行 find_clean_tubes 函数')

    def excute_clean_tubes(self):
        service_control_logger.info('开始执行 excute_clean_tubes 函数')

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

        service_control_logger.info('结束执行 excute_clean_tubes 函数')

    def wash_column(self,wash_time_min,experiment_time_min):

        service_control_logger.info('开始执行 wash_column 函数')

        # self.get_elution_curve()
        # self.write_params()

        # 参数配置

        # D3
        file_path = r'D:\project_python\rotary_evaporator\src\service_control\params.json'

        # D2
        # file_path = r'D:\back\rotary_evaporator\src\service_control\params.json'
        # 加载 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            method = json.load(f)

        # 修改
        method['method']['samplingTime'] = experiment_time_min  # 这里将值改为10，按需修改

        # 写回
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(method, f, ensure_ascii=False, indent=4)

        print(method["method"])
        result = self.sepu_api.update_method(self.method_id, method["method"])
        print("Update Method Result:", result)

        result = self.sepu_api.only_operate()
        print("Only Operate Result:", result)

        result = self.sepu_api.get_line()
        print("Get Line Result:", result)
        # start_time = self.sepu_api.get_current_time()
        # result = self.sepu_api.get_curve(start_time)

        self.sepu_api.column_equilibration(wash_time_min)
        wash_time = wash_time_min * 60 + 5

        time.sleep(wash_time)

        service_control_logger.info('结束执行 wash_column 函数')
        return result

    def update_line_pause(self):
        service_control_logger.info('开始执行 update_line_pause 函数')

        self.sepu_api.update_line_pause()
        time.sleep(5)

        service_control_logger.info('结束执行 update_line_pause 函数')

    def update_line_start(self):

        service_control_logger.info('开始执行 update_line_start 函数')

        self.sepu_api.update_line_start()
        time.sleep(2)

        service_control_logger.info('结束执行 update_line_start 函数')

    def update_line_terminate(self):
        service_control_logger.info('开始执行 update_line_terminate 函数')

        self.sepu_api.update_line_terminate()
        time.sleep(5)

        service_control_logger.info('结束执行 update_line_terminate 函数')

    def start_column(self,experiment_time_min):
        service_control_logger.info('开始执行 start_column 函数')

        #
        # self.sepu_api.set_sample_valve()
        # self.update_line_start()
        time.sleep(experiment_time_min*60 + 5)

        service_control_logger.info('结束执行 start_column 函数')

    def save_experiment_data(self):
        # service_control_logger.info('开始执行 save_experiment_data 函数')
        #
        #
        # # tube = [{'module_id': 1, 'tube_list': [1,2,3,4]}]

        result = self.sepu_api.save_experiment_data()
        print("save_experiment_data",result)

        result = self.sepu_api.save_execution_method()
        print("save_execution_method",result)


        clean_tube = self.sepu_api.get_abandon_tube_tasks()

        print("clean_tube",clean_tube)
        # tube = clean_tube["retain_tubes"]

        if "retain_tubes" in clean_tube:
            tube = clean_tube["retain_tubes"]
        else:
            tube_input = input("未检测到retain_tubes，请手动输入tube（格式如：[{'module_id':1,'tube_list':[1,2,3]}]）：")
            tube = json.loads(tube_input)

        #
        # service_control_logger.info('结束执行 save_experiment_data 函数')
        # # def execute_task(self):
        # service_control_logger.info('开始执行 execute_task 函数')
        #


        for tube_info in tube:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            module_id = tube_info.get('module_id')
            tube_list = tube_info.get('tube_list')


            task_list = {
                "method_id": int(self.sepu_api.method_id),
                "module_id": module_id,  # 由用户输入
                "status": "abandon",
                "task_id": int(timestamp),
                "tube_list": tube_list,  # 由用户输入
            }

            print("任务列表:", task_list)
            result = self.sepu_api.get_tube(task_list)
            print("获取试管结果:")
            print(json.dumps(result, indent=2))
            time.sleep(10)

        while True:
            result = self.sepu_api.get_tube_status()
            print(f"收集液体:", result)
            if result["status"] == True:
                return
            time.sleep(2)

            # threading_cut = threading.Thread(target=execute_task)
            # threading_cut.start()

    def set_start_tube(self,tube_id,module_id):
        self.sepu_api.set_start_tube(tube_id,module_id)
        result = self.sepu_api.get_line()
        start_time = self.sepu_api.get_current_time()
        result = self.sepu_api.get_curve(start_time)

    def get_detected_peaks(self):
        return self.sepu_api.get_detected_peaks()

if __name__ == '__main__':
    sepu = SepuService()
    # print(sepu.get_detected_peaks())
    # sepu.update_line_start()
    tube = [{'module_id': 1, 'tube_list': [1,2,3,4]},{'module_id': 2, 'tube_list': [1,2,3,4]}]
    sepu.sepu_api.get_module_dict(tube)

    # sepu.wash_column(10)
    # sepu.update_line_pause()
    #
    # time.sleep(5)
    #
    # sepu.update_line_start()
    # time.sleep(5)
    #
    # sepu.start_column()
    #
    # sepu.update_line_terminate()
    #
    # sepu.select_retain_tubes()
    # service_control_logger.info('结束执行 execute_task 函数')
    #
    # sepu.save_experiment_data()
