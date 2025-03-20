import time
import json
from src.device_control import robot_controller
from src.uilt.logs_control.setup import service_control_logger

class ApiClient:
    def __init__(self):
        self.method_id = "97"  # 假设 method_id 是 97，可以根据实际情况调整

    def log_and_return(self, step_name, result):
        """ 记录日志并返回结果 """
        log_msg = f"步骤: {step_name}, 状态: {result['status']}, 消息: {result['message']}"
        service_control_logger.info(log_msg)
        return result

    def init_device(self, flag):
        result = {"status": "success", "message": "Device initialized"}
        return self.log_and_return("初始化设备", result)

    def robot_trasfer_flask(self, flask_id_1, flask_id_2):
        robot_controller.trasfer_flask(flask_id_1, flask_id_2)
        result = {"status": "success", "message": f"Robot placed column {flask_id_1}"}
        return self.log_and_return("机器人放色谱柱", result)

    def robot_start_liquid_transfer(self,bottle_id):

        robot_controller.start_liquid_transfer(bottle_id)


        result = {"status": "success", "message": f"Robot placed reagent bottle"}
        return self.log_and_return("机器人放试剂瓶", result)

    def wash_column(self):
        result = ""
        # 以下代码用于方法更新和执行，仅供参考
        # method = {...}  # 这里是色谱柱清洗参数
        # method_id = "97"
        # result = sepu_api.update_method(method_id, method)
        # print("Update Method Result:", result)
        # result = sepu_api.only_operate()
        # print("Only Operate Result:", result)
        # result = sepu_api.get_line()
        # print("Get Line Result:", result)
        # start_time = sepu_api.get_current_time()
        # result = sepu_api.get_curve(start_time)
        return self.log_and_return("冲洗色谱柱", {"status": "success", "message": result})

    def inject_sample(self, volume):
        # 机器人执行进样操作
        # pump_sample.inject(volume, 1, 3)
        result = {"status": "success", "message": f"Robot injected {volume}mL"}
        return self.log_and_return("机器人进样", result)

    def start_column(self):
        # result = sepu_api.set_sample_valve()
        # print("Set Sample Valve Result:")
        result = {"status": "success", "message": "Column operation started"}
        return self.log_and_return("过柱（梯度洗脱）", result)

    def save_experiment_data(self):
        # result = sepu_api.save_experiment_data()
        # print("Save Experiment Data Result:", result)
        result = {"status": "success", "message": "Experiment data saved"}
        return self.log_and_return("保存实验数据", result)

    def robot_evaporate_sample_bottle(self, bottle_id):
        # 机器人执行旋蒸上样
        # print("设备信息：", xuanzheng_controller.get_info())
        # response = xuanzheng_controller.change_device_parameters(...)
        # print("PUT请求响应：", response)
        # xuanzheng_controller.close()
        result = {"status": "success", "message": f"Robot evaporated sample in bottle {bottle_id}"}
        return self.log_and_return("机器人旋蒸上样", result)

    def run_vacuum(self):
        # response = xuanzheng_controller.change_device_parameters(...)
        # print("PUT请求响应：", response)
        # xuanzheng_controller.close()
        pass


    def run_evaporation(self):
        # 旋蒸设备运行
        # response = xuanzheng_controller.change_device_parameters(...)
        # print("PUT请求响应：", response)
        # xuanzheng_controller.close()
        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("旋蒸运行", result)

    def clean_and_reset_collector(self):
        # result = sepu_api.get_tube(task_list)
        # print("Get Tube Result:", json.dumps(result, indent=2))
        result = {"status": "success", "message": "Collector cleaned and reset"}
        return self.log_and_return("收集装置清洗复位", result)

    def robot_collect_evaporated_sample(self, bottle_id):
        # robot_down_sample()
        result = {"status": "success", "message": f"Robot collected evaporated sample from bottle {bottle_id}"}
        return self.log_and_return("机器人旋蒸下样", result)

    def robot_store_sample(self, bottle_id):
        result = {"status": "success", "message": f"Robot stored sample from bottle {bottle_id}"}
        return self.log_and_return("机器人下样，样品入库", result)

    def update_line_terminate(self):
        result = {"status": "success", "message": "Experiment terminated"}
        return self.log_and_return("终止实验", result)

    def robot_remove(self):
        robot_controller.send('ok')

    def peristaltic_pump_transfer_liquid(self):
        pass

    def robot_start_spray(self):
        robot_controller.start_spray()

        pass
    def start_gear_pump(self):
        pass

    def robot_liquid_transfer_finish(self):
        robot_controller.liquid_transfer_finish()
    def robot_start(self):
        robot_controller.start()

def wait_for_enter():
    input("\n按 Enter 继续执行下一步...")

def main():
    api_client = ApiClient()
    bottle_id_map = {1: "1000mL", 2: "200mL"}  # 按照位置分配瓶子大小
    # robot_controller.start_connection_monitor()

    steps = [
        ("初始化设备", lambda: api_client.init_device(True)),
        ("放色谱柱", lambda: api_client.robot_start()),
        ("机器人放试剂瓶", lambda: api_client.robot_trasfer_flask(7,17)),
        # ("冲洗色谱柱", lambda: api_client.wash_column()),
        ("机器人拿针头", lambda: api_client.robot_start_liquid_transfer(1)),
        # ("进样", lambda: api_client.inject_sample(30)),
        ("机器人拿针头", lambda: api_client.robot_liquid_transfer_finish()),

        # ("过柱（梯度洗脱）", lambda: api_client.start_column()),
        # ("人工汇总、清洗", lambda: api_client.save_experiment_data()),
        # ("机器人旋蒸上样（1000mL大瓶）", lambda: api_client.robot_trasfer_flask(3,4)),
        # ("旋蒸抽真空", lambda: api_client.run_vacuum()),
        # ("机器人旋蒸移走", lambda: api_client.robot_remove()),
        #
        # ("旋蒸运行", lambda: api_client.run_evaporation()),
        # ("收集装置清洗复位", lambda: api_client.clean_and_reset_collector()),
        # ("机器人旋蒸下样", lambda: api_client.robot_trasfer_flask(4,5)),
        #
        # ("机器人取样品小瓶（机器人）200mL 小瓶，放到转移工位", lambda: api_client.robot_trasfer_flask(5, 6)),
        # ("机器人转移剩余物质到小瓶按蠕动泵行程控制", lambda: api_client.peristaltic_pump_transfer_liquid()),
        #
        # ("机器人清洗大瓶", lambda: api_client.robot_start_spray()),
        # ("齿轮泵开始转动", lambda: api_client.start_gear_pump()),
        # ("机器人转移剩余物质到小瓶", lambda: api_client.peristaltic_pump_transfer_liquid()),
        #
        # ("机器人清洗大瓶", lambda: api_client.robot_start_spray()),
        # ("齿轮泵开始转动", lambda: api_client.start_gear_pump()),
        # ("机器人转移剩余物质到小瓶", lambda: api_client.peristaltic_pump_transfer_liquid()),

        # ("机器人清洗大瓶", lambda: api_client.robot_start_spray()),
        # ("齿轮泵开始转动", lambda: api_client.start_gear_pump()),
        # ("机器人转移剩余物质到小瓶", lambda: api_client.peristaltic_pump_transfer_liquid()),
        #
        # ("机器人下样，样品入库", lambda: api_client.robot_store_sample(2)),
        # ("终止实验", lambda: api_client.update_line_terminate()),
    ]

    for step_name, action in steps:
        print(f"\n执行步骤: {step_name}")
        result = action()
        print(json.dumps(result, indent=2))
        wait_for_enter()

    print("\n实验流程执行完毕！")

if __name__ == "__main__":
    main()
