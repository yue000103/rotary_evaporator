from com_control.xuanzheng_com import ConnectionController


class ProcessController:
    def __init__(self,mock=False):
        self.connection = ConnectionController(mock)

    def get_info(self):
        return self.connection.send_request("/api/v1/info", method='GET')

    def change_device_parameters(self, heating=None, cooling=None, vacuum=None, rotation=None, lift=None, running=None):
        data = {}

        if heating is not None:
            data["heating"] = {"set": heating["set"], "running": heating.get("running", False)}
        if cooling is not None:
            data["cooling"] = {"set": cooling["set"], "running": cooling.get("running", False)}
        if vacuum is not None:
            data["vacuum"] = {"set": vacuum["set"], "vacuumValveOpen": vacuum.get("vacuumValveOpen", False),
                              "aerateValvePulse": vacuum.get("aerateValvePulse", False)}
        if rotation is not None:
            data["rotation"] = {"set": rotation["set"], "running": rotation.get("running", True)}
        if lift is not None:
            data["lift"] = {"set": lift["set"]}
        data['program'] = {'Type': 'Manual'}
        if running is not None:
            data['globalStatus'] = {'running': running}

        return self.connection.send_request("/api/v1/process", method='PUT', data=data)

    def close(self):
        self.connection.close()


# 使用示例
if __name__ == "__main__":

    # 直接初始化 ProcessController，可选择 mock 模式
    controller = ProcessController(mock=True)  # mock=True 开启模拟模式

    # 获取信息（模拟模式下不会真正发送请求）
    print("设备信息：", controller.get_info())

    # 更改设备参数
    heating = {"set": 30, "running": False}
    cooling = {"set": 10, "running": False}
    vacuum = {"set": 500, "vacuumValveOpen": False, "aerateValvePulse": False}
    rotation = {"set": 60, "running": True}
    lift = {"set": 0}

    response = controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum, rotation=rotation,
                                                   lift=lift)
    print("PUT请求响应：", response)

    controller.close()
