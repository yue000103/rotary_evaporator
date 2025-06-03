MOCK = False


from src.device_control.xuanzheng_device import XuanZHengController

xuanzheng_controller = XuanZHengController(mock=False)  # mock=True 开启模拟模式


from src.device_control.sepu.api_fun import ApiClient
sepu_api = ApiClient()

from src.device_control.pump_sample import PumpSample
pump_sample = PumpSample(mock=MOCK)

from src.device_control.robot_control.robot_device_new import RobotController
robot_controller = RobotController(mock=MOCK)

from src.device_control.peristaltic_pump import PeristalticPump

pump_device = PeristalticPump(mock=MOCK)  # 启用 Mock 模式测试

from src.device_control.gear_pump import GearPump

gear_pump = GearPump(mock=MOCK)  # 启用 Mock 模式测试

from src.device_control.inject_height import InjectHeight
inject_height = InjectHeight(mock=MOCK)