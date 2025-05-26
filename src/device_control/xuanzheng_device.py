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
        """轮询获取旋蒸当前状态，等待其先运行再结束"""

        has_started = False  # 标志位：是否检测到旋蒸运行开始

        try:
            while True:
                raw_result = self.get_process()
                print("当前状态：", raw_result)

                # 判断数据格式
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

                is_running = result.get("globalStatus", {}).get("running", False)

                if is_running:
                    print("设备正在运行...")
                    has_started = True  # 标记设备已经开始运行
                elif has_started:
                    print("检测到运行结束，退出轮询。")
                    break
                else:
                    print("尚未开始运行，继续等待...")

                time.sleep(2)

        except Exception as e:
            print(f"xuanzheng_sync 轮询过程中发生异常: {e}")
        finally:
            print("结束执行 xuanzheng_sync 函数")

    def change_device_parameters(self, heating=None, cooling=None, vacuum=None, rotation=None, lift=None, running=None,
                                 program=None):
        data = {}

        if heating is not None:
            data["heating"] = {
                "set": heating["set"],
                "running": heating.get("running", False)
            }

        if cooling is not None:
            data["cooling"] = {
                "set": cooling["set"],
                "running": cooling.get("running", False)
            }

        if vacuum is not None:
            data["vacuum"] = {
                "set": vacuum["set"],
                "vacuumValveOpen": vacuum.get("vacuumValveOpen", False),
                "aerateValveOpen": vacuum.get("aerateValveOpen", False),
                "aerateValvePulse": vacuum.get("aerateValvePulse", False)
            }

        if rotation is not None:
            data["rotation"] = {
                "set": rotation["set"],
                "running": rotation.get("running", True)
            }

        if lift is not None:
            data["lift"] = {"set": lift["set"]}

        if running is not None:
            data["globalStatus"] = {"running": running}

        if program is not None:
            data["program"] = {
                "type": program.get("type", "AutoDest"),
                "endVacuum": program.get("endVacuum", 0),
                "flaskSize": program.get("flaskSize", 2)
            }

        return self.connection.send_request("/api/v1/process", method='PUT', data=data)

    def close(self):
        self.connection.close()




    def set_height(self,volume):
        #1000 500 100 50
        if volume == 1000:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1050)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 2}
            )

        elif volume == 500:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1150)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 1}
            )
        elif volume == 100:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1332)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 1}
            )
        elif volume == 50:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1417)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 1}
            )
        elif volume == 0:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 0)

        self.plc.write_coil(self.AUTO_SET,True)


        time.sleep(3)
        self.height_finish_async()
        self.plc.write_coil(self.AUTO_SET,False)



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

    def vacuum_until_below_threshold(self, threshold=400):
        """
        启动抽真空，直到 vacuum.act 小于阈值（默认400）后停止。
        """
        print("🌀 开始抽真空")
        self.run_vacuum()

        while True:
            raw_result = self.get_process()
            result = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

            act = result.get("vacuum", {}).get("act", 9999)
            print(f"当前真空值: {act:.1f} mbar")

            if act < threshold:
                print(f"✅ 真空值已低于 {threshold}，停止抽真空")
                self.stop_vacuum()
                break

            time.sleep(1)

    def drain_until_above_threshold(self, threshold=900):
        """
        打开排气阀，直到 vacuum.act 大于阈值（默认900）后等待5秒。
        """
        print("💨 打开排气阀")
        self.drain_valve_open()

        while True:
            raw_result = self.get_process()
            result = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

            act = result.get("vacuum", {}).get("act", 0)
            print(f"当前真空值: {act:.1f} mbar")

            if act > threshold:
                print(f"✅ 真空值已高于 {threshold}，等待 5 秒")
                time.sleep(5)
                break

            time.sleep(1)

    def test_1(self):
        print("test_1 start")
        time.sleep(5)
        print("test_1 end")

    def test_2(self):
        print("test_2 start")
        time.sleep(10)
        print("test_2 end")
    def test_3(self):
        print("test_3 start")
        time.sleep(3)
        print("test_3 end")

# 使用示例
if __name__ == "__main__":

    # 直接初始化 ProcessController，可选择 mock 模式
    controller = XuanZHengController(mock=False)  # mock=True 开启模拟模式
    # controller.xuanzheng_sync()

    # 获取信息（模拟模式下不会真正发送请求）
    print("设备信息：", controller.get_process())

    # controller.change_device_parameters(
    #     program={"type": "AutoDest", "flaskSize": 1}
    # )
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
    # controller.run_vacuum()
    # controller.set_height(100)
    # controller.run_evaporation()
    # controller.xuanzheng_sync()
    # controller.set_height(0)
    # controller.start_waste_liquid()

    # controller.set_auto_set_height(True)
    #
    # controller.set_height(0)
    # print("----------------")
