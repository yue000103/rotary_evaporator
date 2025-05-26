import time

from src.com_control.xuanzheng_com import ConnectionController
from src.com_control.PLC_com import PLCConnection
import json


class XuanZHengController:
    def __init__(self,mock=False):
        self.connection = ConnectionController(mock)
        self.plc = PLCConnection(mock=mock)
        self.HEIGHT_ADDRESS = 502
        self.AUTO_SET = 500
        self.AUTO_FINISH = 501
        self.WASTE_LIQUID = 323
        self.WASTE_LIQUID_FINISH = 333



    def get_info(self):
        return self.connection.send_request("/api/v1/info", method='GET')

    def get_process(self):
        return self.connection.send_request("/api/v1/process", method='GET')

    def xuanzheng_sync(self):
        """轮询获取旋蒸当前状态，直到运行结束"""

        try:
            while True:
                raw_result = self.get_process()  # 假设该方法返回的是你提供的 JSON 状态
                print("当前状态：", raw_result)

                if isinstance(raw_result, str):
                    try:
                        result = json.loads(raw_result)
                    except json.JSONDecodeError as e:
                        print(f"JSON 解析失败: {e}")
                        break
                elif isinstance(raw_result, dict):
                    result = raw_result
                else:
                    print("未知的返回类型，既不是 str 也不是 dict，退出")
                    break

                # 取出 globalStatus.running，如果为 False，则表示任务完成，退出循环
                is_running = result.get("globalStatus", {}).get("running", False)
                if not is_running:
                    print("设备运行已结束，退出轮询。")
                    break

                time.sleep(2)
        except Exception as e:
            print(f"xuanzheng_sync 轮询过程中发生异常: {e}")
        finally:
            print("结束执行 xuanzheng_sync 函数")


    def change_device_parameters(self, heating=None, cooling=None, vacuum=None, rotation=None, lift=None, running=None):
        # self.get_info()
        data = {}

        if heating is not None:
            data["heating"] = {"set": heating["set"], "running": heating.get("running", False)}
        if cooling is not None:
            data["cooling"] = {"set": cooling["set"], "running": cooling.get("running", False)}
        if vacuum is not None:
            data["vacuum"] = {"set": vacuum["set"], "vacuumValveOpen": vacuum.get("vacuumValveOpen", False),
                              "aerateValveOpen": vacuum.get("aerateValveOpen", False),
                              "aerateValvePulse": vacuum.get("aerateValvePulse", False)}
        if rotation is not None:
            data["rotation"] = {"set": rotation["set"], "running": rotation.get("running", True)}
        if lift is not None:
            data["lift"] = {"set": lift["set"]}
        # data['program'] = {'Type': 'Manual'}
        if running is not None:
            data['globalStatus'] = {'running': running}


        return self.connection.send_request("/api/v1/process", method='PUT', data=data)

    def close(self):
        self.connection.close()

    def set_height(self,volume):
        #1000 500 100 50
        self.plc.write_coil(self.AUTO_SET,True)
        if volume == 1000:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1050)

        elif volume == 500:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1150)
        elif volume == 100:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1332)
        elif volume == 50:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1417)
        elif volume == 0:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 0)

        time.sleep(3)
        self.height_finish_async()


    def set_auto_set_height(self,flag:bool):
        self.plc.write_coil(self.AUTO_SET,flag)

    def height_finish_async(self):
        while True:
            print("-----------height_finish_async----------")
            done = self.plc.read_coils(self.AUTO_FINISH,1)[0]
            if done:
                return True
    def start_waste_liquid(self):
        self.plc.write_coil(self.WASTE_LIQUID, True)
        time.sleep(1)
        self.plc.write_coil(self.WASTE_LIQUID, False)
        time.sleep(2)
        self.waste_finish_async()

    def waste_finish_async(self):
        while True:
            done = self.plc.read_coils(self.WASTE_LIQUID_FINISH)[0]
            # print(done)
            if done:
                return True
            time.sleep(1)


        # pass
        # self.plc.write_coil(self.HEIGHT_ADDRESS, True)

    # def set_height_up(self):
    #     # self.plc.write_single_register(self.HEIGHT_ADDRESS, height)
    #     self.plc.write_coil(self.HEIGHT_ADDRESS, False)

        #307

    def run_vacuum(self):
        heating = None
        cooling = None
        vacuum = {"set": 150, "vacuumValveOpen": True, "aerateValveOpen": False}
        rotation = None
        lift = {"set": 0}
        globalStatus = None

        response = self.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=None)
        print("PUT请求响应：", response)

        time.sleep(10)

        self.stop_vacuum()

    def stop_vacuum(self):
        heating = None
        cooling = None
        vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": False}
        rotation = None
        lift = {"set": 0}
        globalStatus = None

        response = self.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=None)
        print("PUT请求响应：", response)

    def run_evaporation(self):
        running = True
        # globalStatus = None

        response = self.change_device_parameters(heating=None, cooling=None, vacuum=None,
                                                                  rotation=None,
                                                                 lift=None, running=running)
        time.sleep(10)

        print("PUT请求响应：", response)


    def stop_evaporation(self):
        running = False
        # globalStatus = None

        response = self.change_device_parameters(heating=None, cooling=None, vacuum=None,
                                                                 rotation=None,
                                                                 lift=None, running=running)
        print("PUT请求响应：", response)

    def drain_valve_open(self):
        vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": True, "aerateValvePulse": False}

        # globalStatus = None

        response = self.change_device_parameters(heating=None, cooling=None, vacuum=vacuum,
                                                                 rotation=None,
                                                                 lift=None, running=None)
        print("PUT请求响应：", response)
        time.sleep(5)

# 使用示例
if __name__ == "__main__":

    # 直接初始化 ProcessController，可选择 mock 模式
    controller = XuanZHengController(mock=False)  # mock=True 开启模拟模式
    # controller.xuanzheng_sync()

    # 获取信息（模拟模式下不会真正发送请求）
    # print("设备信息：", controller.get_process())
    # 隔个1分钟get一次
    # controller.set_height(0)

    # # 更改设备参数
    # heating = {"set": 30, "running": False}
    # cooling = {"set": 10, "running": False}
    # vacuum = {"set": 500, "vacuumValveOpen": False, "aerateValveOpen": True,"aerateValvePulse":True}
    # # rotation = {"set": 60, "running": False}
    # lift = {"set": 0}
    # globalStatus = {"running": True}

    # heating = None
    # cooling = None
    # vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": False}
    # rotation = None
    # lift = {"set": 0}
    # globalStatus = None

    # response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
    #                                                          rotation=rotation,
    #                                                          lift=lift, running=None)
    # globalStatus = None
    #
    # response = controller.change_device_parameters(heating=None, cooling=None, vacuum=vacuum, rotation=None,
    #                                                lift=None,running=False)
    # print("PUT请求响应：", response)

    # controller.close()
    # controller.waste_finish_async()
    controller.run_evaporation()
    controller.xuanzheng_sync()

    # controller.set_auto_set_height(True)
    #
    # controller.set_height(0)
    # print("----------------")
