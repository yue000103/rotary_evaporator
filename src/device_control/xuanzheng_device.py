import time

from src.com_control.xuanzheng_com import ConnectionController
from src.com_control.PLC_com import PLCConnection


class ProcessController:
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



# 使用示例
if __name__ == "__main__":

    # 直接初始化 ProcessController，可选择 mock 模式
    controller = ProcessController(mock=False)  # mock=True 开启模拟模式

    # 获取信息（模拟模式下不会真正发送请求）
    print("设备信息：", controller.get_process())
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
    controller.waste_finish_async()
