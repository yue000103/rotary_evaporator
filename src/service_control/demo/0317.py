import time
import json
from src.device_control import (robot_controller,sepu_api,pump_sample,
                                xuanzheng_controller,pump_device,gear_pump,
                                inject_height)
from src.uilt.logs_control.setup import service_control_logger
import threading

from src.service_control.sepu.sepu_service import SepuService
sepu_service = SepuService()



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
        # method = {
        #     "samplingTime": 5,
        #     "detectorWavelength": 258,
        #     "equilibrationColumn": 1,
        #     "speed": 100,
        #     "totalFlowRate": 10,
        #     "cleanList": [
        #         {
        #             "module_id": 2,
        #             "liquid_volume": 10,
        #             "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        #         },
        #         {
        #             "module_id": 1,
        #             "liquid_volume": 10,
        #             "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        #         }
        #     ],
        #     "cleaningCount": 2,
        #     "cleaningSpeed": None,
        #     "drainSpeed": None,
        #     "isocratic": 0,
        #     "methodName": "12",
        #     "pressure": 1,
        #     "pumpA": None,
        #     "pumpB": None,
        #     "pumpList": [
        #         {"time": 0, "pumpB": 100, "pumpA": 0, "flowRate": 40},
        #         {"time": 1, "pumpB": 100, "pumpA": 0, "flowRate": 40},
        #         {"time": 2, "pumpB": 0, "pumpA": 100, "flowRate": 40},
        #         {"time": 3, "pumpB": 0, "pumpA": 100, "flowRate": 40},
        #         {"time": 4, "pumpB": 0, "pumpA": 100, "flowRate": 40},
        #         {'time': 5, "pumpB": 0, "pumpA": 100, "flowRate": 40},
        #     ],
        #     "retainList": [
        #         {
        #             "module_id": 1,
        #             "liquid_volume": 30,
        #             "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        #         },
        #         {
        #             "module_id": 2,
        #             "liquid_volume": 30,
        #             "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        #         }
        #     ],
        #     "smiles": "4896",
        # }
        # method_id = "97"
        # result = sepu_api.update_method(method_id, method)
        # print("Update Method Result:", result)
        # result = sepu_api.only_operate()
        # print("Only Operate Result:", result)
        # result = sepu_api.get_line()
        # print("Get Line Result:", result)
        # start_time = sepu_api.get_current_time()
        # result = sepu_api.get_curve(start_time)
        result = sepu_service.wash_column()
        return self.log_and_return("冲洗色谱柱", {"status": "success", "message": result})
    def select_tube_retain(self):
        # sepu_service.get_experiment_data()
        message = sepu_service.select_retain_tubes()
        result = {"status": "success", "message": message}

        return self.log_and_return("人选择保留的试管", result)

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
            print(result)
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
        # print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        heating = None
        cooling = None
        vacuum = {"set": 150, "vacuumValveOpen": True, "aerateValveOpen": False}
        rotation = None
        lift = {"set": 0}
        globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                       rotation=rotation,
                                                       lift=lift, running=None)
        print("PUT请求响应：", response)

        time.sleep(10)

        self.stop_vacuum()

        # xuanzheng_controller.close()

    def stop_vacuum(self):
        heating = None
        cooling = None
        vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": False}
        rotation = None
        lift = {"set": 0}
        globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=None)
        print("PUT请求响应：", response)



    def run_evaporation(self):
        # 获取信息（模拟模式下不会真正发送请求）
        # print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        # heating = {"set": 30, "running": True}
        # cooling = {"set": 0, "running": True}

        running =  True
        # globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=None, cooling=None, vacuum=None,
                                                                 rotation=None,
                                                                 lift=None, running=running)
        print("PUT请求响应：", response)

        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("旋蒸运行", result)

    def stop_evaporation(self):
        # 获取信息（模拟模式下不会真正发送请求）
        # print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数
        # heating = {"set": 30,"running": True}
        # cooling = {"set": 0,"running": True}
        # vacuum = { "set": 500,"vacuumValveOpen": False}
        # rotation = {"set": 60,"running": False}
        # lift = {"set": 0}
        running = False
        # globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=None, cooling=None, vacuum=None,
                                                                 rotation=None,
                                                                 lift=None, running=running)
        print("PUT请求响应：", response)

        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("停止悬蒸", result)

    def drain_valve_open(self):
        # 获取信息（模拟模式下不会真正发送请求）
        # print("设备信息：", xuanzheng_controller.get_info())
        # 隔个1分钟get一次
        # 更改设备参数

        vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": True,"aerateValvePulse":False}

        # globalStatus = None

        response = xuanzheng_controller.change_device_parameters(heating=None, cooling=None, vacuum=vacuum,
                                                                 rotation=None,
                                                                 lift=None, running=None)
        print("PUT请求响应：", response)

        result = {"status": "success", "message": "Evaporation process running"}
        return self.log_and_return("排空阀打开关闭", result)

    def clean_and_reset_collector(self):
        # timestamp = time.strftime("%Y%m%d%H%M%S")
        # task_list = {
        #     "method_id": int(sepu_api.method_id),
        #     "module_id": 1,
        #     "status": "clean",
        #     "task_id": int(timestamp),
        #     "tube_list": [1, 2,]
        # }
        #
        # print("task_list", task_list)
        # result = sepu_api.get_tube(task_list)
        # print("Get Tube Result:")
        # print(json.dumps(result, indent=2))
        sepu_service.find_clean_tubes()
        sepu_service.excute_clean_tubes()

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
        # pump_device.set_speed(300)
        pump_device.start_pump()
        result = {"status": "success", "message": "Start Peristaltic"}
        return self.log_and_return("机器人转移剩余物质到小瓶（蠕动泵）", result)
        pass
    def stop_peristaltic_pump(self):
        pump_device.stop_pump()
        result = {"status": "success", "message": "Stop Peristaltic"}
        return self.log_and_return("停止蠕动泵", result)
    def robot_start_spray(self):
        robot_controller.start_spray()
        result = {"status": "success", "message": "Stop Gear"}
        return self.log_and_return("终止实验", result)

        pass
    def start_gear_pump(self):
        time_s = int(float(input("请输入秒数")) * 1000)
        gear_pump.start_pump(time_s)
        # time.sleep(2)
        # gear_pump.stop_pump()
        result = {"status": "success", "message": "Start Gear"}
        return self.log_and_return("终止实验", result)
        pass

    def robot_liquid_transfer_finish(self):
        robot_controller.inject_sample_finish()

        result = {"status": "success", "message": "Robot Transfer"}
        return self.log_and_return("液体转移成功", result)
    def robot_start(self):
        robot_controller.start()
        result = {"status": "success", "message": "Robot start"}
        return self.log_and_return("机械臂开始", result)

    def down_collect_needle(self):
        # robot_controller.down_collect_needle()


        result = {"status": "success", "message": "Down Collect Needle"}
        return self.log_and_return("讲下收集针", result)

    def rise_collect_needle(self):
        # robot_controller.rise_collect_needle()
        result = {"status": "success", "message": "Rise Collect Needle"}
        return self.log_and_return("升起收集针", result)




def wait_for_enter():
    input("\n按 Enter 继续执行下一步...")

def main():
    api_client = ApiClient()
    bottle_id_map = {1: "1000mL", 2: "200mL"}  # 按照位置分配瓶子大小

    steps = {
        1: ("设置自动调高度", lambda: xuanzheng_controller.set_auto_set_height(True)),
        2: ("机械臂开始", lambda: api_client.robot_start()),
        # 3: ("机器人放试剂瓶", lambda: api_client.robot_trasfer_flask(7, 17)),
        4: ("冲洗色谱柱", lambda: api_client.wash_column()),
        5: ("暂停实验", lambda: sepu_api.update_line_pause()),
        6: ("进样", lambda: api_client.inject_sample(10000)),
        7: ("机器人拿针头去清洗", lambda: api_client.robot_liquid_transfer_finish()),
        8: ("进样", lambda: api_client.inject_sample(30000)),
        9: ("机器人拿走针头", lambda: robot_controller.robot_change_gripper()),
        50:("开始加洗针液体", lambda: pump_device.start_washing_liquid()),
        51: ("开始废弃洗针液体", lambda: pump_device.start_waste_liquid()),

        10: ("继续实验",lambda: sepu_api.update_line_start()),
        11: ("过柱（梯度洗脱）", lambda: api_client.start_column()),
        12: ("终止实验", lambda: api_client.update_line_terminate()),
        13: ("降下收集针", lambda: inject_height.down_height()),
        # 14: ("人工汇总、清洗", lambda: prompt_and_save_experiment_data(api_client)),
        14:("人工汇总、清洗", lambda: api_client.select_tube_retain()),
        15: ("升起收集针", lambda: inject_height.up_height()),
        16: ("机器人旋蒸上样（1000mL大瓶）", lambda: robot_controller.robot_change_gripper()),
        17: ("旋蒸抽真空", lambda: api_client.run_vacuum()),
        18: ("机器人旋蒸移走", lambda: robot_controller.robot_change_gripper()),
        19: ("调高度", lambda: xuanzheng_controller.set_height(1000)),
        20: ("旋蒸运行", lambda: api_client.run_evaporation()),
        21: ("收集装置清洗复位", lambda: api_client.clean_and_reset_collector()),
        22: ("旋蒸停止运行", lambda: api_client.stop_evaporation()),

        23: ("调高度", lambda: xuanzheng_controller.set_height(0)),
        24: ("机械臂去旋蒸", lambda: robot_controller.robot_change_gripper()),
        25: ("排空阀打开", lambda: api_client.drain_valve_open()),
        26: ("机器人旋蒸下样", lambda: robot_controller.robot_change_gripper()),

        48: ("喷淋溶解", lambda: api_client.start_gear_pump()),
        49: ("机器人摇匀", lambda: robot_controller.robot_change_gripper()),

        27: ("机器人转移剩余物质到小瓶（蠕动泵）", lambda: api_client.peristaltic_pump_transfer_liquid()),

        28: ("机器人换喷淋头，第一次清洗", lambda: robot_controller.robot_change_gripper()),
        29: ("齿轮泵开始转动", lambda: api_client.start_gear_pump()),
        30: ("机器人换针头", lambda: robot_controller.robot_change_gripper()),
        31: ("机器人转移剩余物质到小瓶（蠕动泵）", lambda: api_client.peristaltic_pump_transfer_liquid()),

        32: ("机器人换喷淋头，第二次清洗", lambda: robot_controller.robot_change_gripper()),
        33: ("齿轮泵开始转动", lambda: api_client.start_gear_pump()),
        34: ("机器人换针头", lambda: robot_controller.robot_change_gripper()),
        35: ("机器人转移剩余物质到小瓶（蠕动泵）", lambda: api_client.peristaltic_pump_transfer_liquid()),

        36: ("空白", lambda: api_client.down_collect_needle()),


        37: ("机器人旋蒸上样（小瓶）", lambda: robot_controller.robot_change_gripper()),
        38: ("旋蒸抽真空", lambda: api_client.run_vacuum()),

        39: ("机器人旋蒸移走", lambda: robot_controller.robot_change_gripper()),
        40: ("小瓶调高度", lambda: xuanzheng_controller.set_height(50)),
        41: ("旋蒸运行", lambda: api_client.run_evaporation()),
        42: ("空白", lambda: api_client.down_collect_needle()),
        43: ("旋蒸停止运行", lambda: api_client.stop_evaporation()),
        44: ("小瓶调高度", lambda: xuanzheng_controller.set_height(0)),
        45: ("机器人旋蒸下样", lambda: robot_controller.robot_change_gripper()),
        46: ("排空阀打开关闭", lambda: api_client.drain_valve_open()),
        47: ("机器人旋蒸下样", lambda: robot_controller.robot_change_gripper()),
        60: ("开始废弃旋蒸废液", lambda: xuanzheng_controller.start_waste_liquid())
    }

    step_num = None
    while True:
        print("\n请选择要执行的步骤:")
        for key, (desc, _) in steps.items():
            print(f"{key}: {desc}")
        print("next: 执行下一个步骤")
        print("0: 退出")

        choice = input("请输入步骤编号或 'next' 继续: ")

        if choice == "0":
            print("退出程序。")
            xuanzheng_controller.close()
            break
        elif choice.lower() == "next":
            if step_num is None:
                step_num = 1
            else:
                step_num += 1
        else:
            try:
                step_num = int(choice)
            except ValueError:
                print("请输入有效的数字或 'next' 继续。")
                continue

        if step_num in steps:
            print(f"正在执行: {steps[step_num][0]}")
            result = steps[step_num][1]()
            print(json.dumps(result, indent=2))
        else:
            print("输入错误，请重新输入。")

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

# def prompt_and_clean_and_reset_collector(api_client):
#     """
#     该函数用于在人工汇总、清洗步骤前，输入试管号和模块号，并传递给 save_experiment_data 函数
#     """
#     while True:
#         try:
#             tube_list = input("请输入试管号（多个用逗号分隔，例如 1,2,3）：").strip()
#             module_id = int(input("请输入模块号（例如 1）：").strip())
#             tube_list = [int(tube) for tube in tube_list.split(",")]
#             break
#         except ValueError:
#             print("输入错误，请重新输入正确的数值。")
#
#     print(f"试管号: {tube_list}，模块号: {module_id}，正在执行保存实验数据...")
#
#     result = api_client.save_experiment_data(module_id, tube_list)
#     print(json.dumps(result, indent=2))
#


if __name__ == "__main__":
    main()
