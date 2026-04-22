import logging
import time

from src.com_control import plc
from src.uilt.logs_control.setup import device_control_logger


class InjectHeight:
    def __init__(self, mock=False):
        """
        Injection height control class based on Modbus communication
        :param mock: Whether to enable Mock mode
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock

        self.REG_START_START = 307

    def down_height(self):
        print("Lowering needle down_height")
        self.plc.write_coil(self.REG_START_START, True)
        time.sleep(1)

    def up_height(self):
        print("Raising needle up_height")

        self.plc.write_coil(self.REG_START_START, False)
        time.sleep(1)







if __name__ == '__main__':
    height = InjectHeight(mock=False)

    height.up_height()

