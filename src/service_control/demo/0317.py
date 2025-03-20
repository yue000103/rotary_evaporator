import time
import json
from src.device_control import robot_controller,sepu_api,pump_sample,xuanzheng_controller,pump_device,gear_pump
from src.uilt.logs_control.setup import service_control_logger
import threading

class ApiClient:
    def __init__(self):
        self.method_id = "97"  # 假设 method_id 是 97，可以根据实际情况调整

    def log_and_return(self, step_name, result):
        """ 记录日志并返回结果 """
        log_msg = f"步骤: {step_name}, 状态: {result['status']}, 消息: {result['message']}"
        service_control_logger.info(log_msg)
        return result

    def init_device(self, flag):
        sepu_api.init_device(flag)
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
        result = sepu_api.update_method(method_id, method)
        print("Update Method Result:", result)
        result = sepu_api.only_operate()
        print("Only Operate Result:", result)
        result = sepu_api.get_line()
        print("Get Line Result:", result)
        start_time = sepu_api.get_current_time()
        result = sepu_api.get_curve(start_time)
        return self.log_and_return("冲洗色谱柱", {"status": "success", "message": result})

    def inject_sample(self, volume):
        # 机器人执行进样操作
        pump_sample.inject(volume, 1, 3)

        result = {"status": "success", "message": f"Robot injected {volume}mL"}
        return self.log_and_return("机器人进样", result)

    def start_column(self):
        result = sepu_api.set_sample_valve()
        print("Set Sample Valve Result:")
        result = {"status": "success", "message": "Column operation started"}
        return self.log_and_return("过柱（梯度洗脱）", result)

    def save_experiment_data(self, module_id, tube_list):
        def execute_task():
            result = sepu_api.save_experiment_data()
            timestamp = time.strftime("%Y%m%d%H%M%S")
            task_list = {
                "method_id": int(sepu_api.method_id),
                "module_id": module_id,  # 由用户输入
                "status": "retain",
                "task_id": int(timestamp),
                "tube_list": tube_list,  # 由用户输入
            }

            print("任务列表:", task_list)
            result = sepu_api.get_tube(task_list)
            print("获取试管结果:")
            print(json.dumps(result, indent=2))

        threading_cut = threading.Thread(target=execute_task)
        threading_cut.start()
        result = {"status": "success", "message": "实验数据已保存"}
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

        # 获取信息（模拟模式下不会真正发送请求）
        print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        heating = {"set": 30, "running": False}
        cooling = {"set": 10, "running": False}
        vacuum = {"set": 500, "vacuumValveOpen": True, "aerateValvePulse": False}
        rotation = {"set": 60, "running": False}
        lift = {"set": 0}
        # globalStatus = {"running": False}
        globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                       rotation=rotation,
                                                       lift=lift, running=None)
        print("PUT请求响应：", response)

        xuanzheng_controller.close()




    def run_evaporation(self):
        # 获取信息（模拟模式下不会真正发送请求）
        print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        heating = {"set": 30, "running": False}
        cooling = {"set": 10, "running": False}
        vacuum = {"set": 500, "vacuumValveOpen": False, "aerateValvePulse": False}
        rotation = {"set": 60, "running": False}
        lift = {"set": 0}
        globalStatus = {"running": True}
        # globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=globalStatus)
        print("PUT请求响应：", response)

        xuanzheng_controller.close()
        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("旋蒸运行", result)

    def stop_evaporation(self):
        # 获取信息（模拟模式下不会真正发送请求）
        print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        heating = {"set": 30, "running": False}
        cooling = {"set": 10, "running": False}
        vacuum = {"set": 500, "vacuumValveOpen": False, "aerateValvePulse": False}
        rotation = {"set": 60, "running": False}
        lift = {"set": 0}
        globalStatus = {"running": False}
        # globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=globalStatus)
        print("PUT请求响应：", response)

        xuanzheng_controller.close()
        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("旋蒸运行", result)

    def drain_valve_open(self):
        # 获取信息（模拟模式下不会真正发送请求）
        print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        heating = {"set": 30, "running": False}
        cooling = {"set": 10, "running": False}
        vacuum = {"set": 500, "vacuumValveOpen": False, "aerateValvePulse": True}
        rotation = {"set": 60, "running": False}
        lift = {"set": 0}
        globalStatus = {"running": False}
        # globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=None)
        print("PUT请求响应：", response)

        xuanzheng_controller.close()
        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("旋蒸运行", result)

    def clean_and_reset_collector(self):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        task_list = {
            "method_id": int(sepu_api.method_id),
            "module_id": 1,
            "status": "clean",
            "task_id": int(timestamp),
            "tube_list": [1, 2, 3, 4, 5, 6, 7, 8]
        }

        print("task_list", task_list)
        result = sepu_api.get_tube(task_list)
        print("Get Tube Result:")
        print(json.dumps(result, indent=2))

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
        sepu_api.update_line_terminate()
        result = {"status": "success", "message": "Experiment terminated"}
        return self.log_and_return("终止实验", result)

    def robot_remove(self):
        robot_controller.send_ok()
        result = {"status": "success", "message": "Robot Remove"}
        return self.log_and_return("终止实验", result)

    def peristaltic_pump_transfer_liquid(self):
        pump_device.set_speed(500)
        pump_device.start_pump()
        result = {"status": "success", "message": "Start Peristaltic"}
        return self.log_and_return("终止实验", result)
        pass
    def stop_peristaltic_pump(self):
        pump_device.stop_pump()
        result = {"status": "success", "message": "Stop Peristaltic"}
        return self.log_and_return("终止实验", result)
    def robot_start_spray(self):
        robot_controller.start_spray()
        result = {"status": "success", "message": "Stop Gear"}
        return self.log_and_return("终止实验", result)

        pass
    def start_gear_pump(self,time_s):
        gear_pump.start_pump(time_s)
        # time.sleep(2)
        # gear_pump.stop_pump()
        result = {"status": "success", "message": "Start Gear"}
        return self.log_and_return("终止实验", result)
        pass

    def robot_liquid_transfer_finish(self):
        robot_controller.liquid_transfer_finish()
        result = {"status": "success", "message": "Robot Transfer"}
        return self.log_and_return("液体转移成功", result)
    def robot_start(self):
        robot_controller.start()
        result = {"status": "success", "message": "Robot start"}
        return self.log_and_return("机械臂开始", result)

    def down_collect_needle(self):
        robot_controller.down_collect_needle()
        result = {"status": "success", "message": "Down Collect Needle"}
        return self.log_and_return("讲下收集针", result)

    def rise_collect_needle(self):
        robot_controller.rise_collect_needle()
        result = {"status": "success", "message": "Rise Collect Needle"}
        return self.log_and_return("升起收集针", result)




def wait_for_enter():
    input("\n按 Enter 继续执行下一步...")

def main():
    api_client = ApiClient()
    bottle_id_map = {1: "1000mL", 2: "200mL"}  # 按照位置分配瓶子大小

    steps = [
        ("初始化设备", lambda: api_client.init_device(True)),
        ("放色谱柱", lambda: api_client.robot_start()),
        ("机器人放试剂瓶", lambda: api_client.robot_trasfer_flask(7, 17)),
        ("冲洗色谱柱", lambda: api_client.wash_column()),
        ("机器人拿针头", lambda: api_client.robot_start_liquid_transfer(1)),
        ("进样", lambda: api_client.inject_sample(30)),
        ("机器人拿针头", lambda: api_client.robot_liquid_transfer_finish()),
        ("过柱（梯度洗脱）", lambda: api_client.start_column()),
        ("终止实验", lambda: api_client.update_line_terminate()),
        ("降下收集针", lambda: api_client.down_collect_needle()),

        # 人工汇总、清洗前，需要输入试管号和模块号
        ("人工汇总、清洗", lambda: prompt_and_save_experiment_data(api_client)),

        ("升起收集针", lambda: api_client.rise_collect_needle()),
        ("机器人旋蒸上样（1000mL大瓶）", lambda: api_client.robot_trasfer_flask(3, 4)),
        ("旋蒸抽真空", lambda: api_client.run_vacuum()),
        ("机器人旋蒸移走", lambda: api_client.robot_remove()),
        ("旋蒸运行", lambda: api_client.run_evaporation()),
        ("调高度", lambda: xuanzheng_controller.set_height(20)),
        ("收集装置清洗复位", lambda: api_client.clean_and_reset_collector()),
        ("调高度", lambda: xuanzheng_controller.set_height(20)),
        ("旋蒸停止运行", lambda: api_client.stop_evaporation()),
        ("排空阀打开关闭", lambda: api_client.drain_valve_open()),
        ("机器人旋蒸下样", lambda: api_client.robot_trasfer_flask(4, 5)),
        ("机器人取样品小瓶（200mL 小瓶）放到转移工位", lambda: api_client.robot_trasfer_flask(5, 6)),

        ("换夹具", lambda: robot_controller.robot_change_gripper()),
        ("机器人转移剩余物质到小瓶（蠕动泵）", lambda: api_client.peristaltic_pump_transfer_liquid()),
        ("机器人清洗大瓶", lambda: api_client.robot_start_spray()),
        ("齿轮泵开始转动", lambda: api_client.start_gear_pump(2)),
        ("换夹具", lambda: robot_controller.robot_change_gripper()),
        ("机器人转移剩余物质到小瓶", lambda: api_client.peristaltic_pump_transfer_liquid()),
        ("停止蠕动泵", lambda: api_client.stop_peristaltic_pump()),

        ("机器人清洗大瓶", lambda: api_client.robot_start_spray()),
        ("齿轮泵开始转动", lambda: api_client.start_gear_pump()),
        ("机器人转移剩余物质到小瓶", lambda: api_client.peristaltic_pump_transfer_liquid()),
        ("停止蠕动泵", lambda: api_client.stop_peristaltic_pump()),

        ("机器人旋蒸上样（小瓶）", lambda: api_client.robot_trasfer_flask(3, 4)),
        ("旋蒸抽真空", lambda: api_client.run_vacuum()),
        ("机器人旋蒸移走", lambda: api_client.robot_remove()),
        ("旋蒸运行", lambda: api_client.run_evaporation()),
        ("调高度", lambda: xuanzheng_controller.set_height(20)),
        ("收集装置清洗复位", lambda: api_client.clean_and_reset_collector()),
        ("调高度", lambda: xuanzheng_controller.set_height(0)),
        ("旋蒸停止运行", lambda: api_client.stop_evaporation()),

        ("机器人旋蒸下样", lambda: api_client.robot_trasfer_flask(4, 5)),
        ("排空阀打开关闭", lambda: api_client.drain_valve_open()),
        ("机器人旋蒸下样", lambda: api_client.robot_trasfer_flask(4, 5)),

        ("机器人下样，样品入库", lambda: api_client.robot_store_sample(2)),
    ]

    for step_name, action in steps:
        input(f"\n准备执行步骤: {step_name}，输入 'next' 继续... ")
        print(f"正在执行步骤: {step_name}")
        result = action()
        print(json.dumps(result, indent=2))

    print("\n实验流程执行完毕！")

def prompt_and_save_experiment_data(api_client):
    """
    该函数用于在人工汇总、清洗步骤前，输入试管号和模块号，并传递给 save_experiment_data 函数
    """
    while True:
        try:
            tube_list = input("请输入试管号（多个用逗号分隔，例如 1,2,3）：").strip()
            module_id = int(input("请输入模块号（例如 1）：").strip())
            tube_list = [int(tube) for tube in tube_list.split(",")]
            break
        except ValueError:
            print("输入错误，请重新输入正确的数值。")

    print(f"试管号: {tube_list}，模块号: {module_id}，正在执行保存实验数据...")

    result = api_client.save_experiment_data(module_id, tube_list)
    print(json.dumps(result, indent=2))



if __name__ == "__main__":
    main()
