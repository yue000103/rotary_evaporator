import logging
import time

from src.com_control.PLC_com import PLCConnection
from src.uilt.logs_control.setup import device_control_logger


class InjectHeight:
    def __init__(self, mock=False):
        """
        蠕动泵控制类，基于 Modbus 通信
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        self.plc = PLCConnection(mock=mock)

        # 定义寄存器地址
        self.REG_START_START = 307
        self.REG_START_STOP = 306  # 泵启停 (bool)


    def down_height(self):

        #写时间
        # self.plc.write_coil(self.REG_START_START, False)
        # time.sleep(1)
        self.plc.write_coil(self.REG_START_START, True)
        time.sleep(1)



    def up_height(self):
        # self.plc.write_coil(self.REG_START_STOP, False)
        # time.sleep(1)
        # self.plc.write_coil(self.REG_START_STOP, True)
        # time.sleep(1)
        self.plc.write_coil(self.REG_START_START, False)
        time.sleep(1)







if __name__ == '__main__':
    height = InjectHeight(mock=False)  # 启用 Mock 模式测试

    # height.down_height()  # 启动泵

    height.up_height()  #

