MOCK = False


# from src.device_control.xuanzheng_device import ProcessController
#
# xuanzheng_controller = ProcessController(mock=MOCK)  # mock=True 开启模拟模式
#
#
# from src.device_control.sepu.api_fun import ApiClient
# sepu_api = ApiClient()
#
# from src.device_control.pump_sample import PumpSample
# pump_sample = PumpSample()

from src.device_control.robot_device import RobotController
robot_controller = RobotController(mock=MOCK)