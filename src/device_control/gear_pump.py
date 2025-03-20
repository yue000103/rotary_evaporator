import logging
import time

from src.com_control.PLC_com import PLCConnection
from src.uilt.logs_control.setup import device_control_logger


class GearPump:
    def __init__(self, mock=False):
        """
        蠕动泵控制类，基于 Modbus 通信
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        self.plc = PLCConnection(mock=mock)

        # 定义寄存器地址
        self.REG_START_START = 99
        self.REG_START_STOP = 99  # 泵启停 (bool)


    def start_pump(self):
        """ 启动蠕动泵 """

        self.plc.write_coil(self.REG_START_START, False)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_START, True)


    def stop_pump(self):
        """ 停止蠕动泵 """
        self.plc.write_coil(self.REG_START_STOP, False)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_STOP, True)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_STOP, False)






if __name__ == '__main__':
    pump = GearPump(mock=True)  # 启用 Mock 模式测试

    pump.start_pump()  # 启动泵

    pump.stop_pump()  # 停止泵

