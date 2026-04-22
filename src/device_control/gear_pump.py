import logging
import time

from src.com_control import plc
from src.uilt.logs_control.setup import device_control_logger


class GearPump:
    def __init__(self, mock=False):
        """
        Gear pump control class based on Modbus communication
        :param mock: Whether to enable Mock mode
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock

        self.REG_START_START = 306
        self.REG_TIME_S = 102
        self.PUMP_FINISH = 316

    def start_pump(self,time_s):
        time_ms = time_s * 1000
        self.plc.write_coil(self.REG_START_START, True)
        time.sleep(1)
        self.plc.write_dint_register(self.REG_TIME_S, time_ms)

        time.sleep(2)
        self.pump_finish_async()

    def pump_finish_async(self):
        while True:
            done = self.plc.read_coils(self.PUMP_FINISH)[0]
            if done:
                return True
            time.sleep(1)











if __name__ == '__main__':
    pump = GearPump(mock=False)

    pump.start_pump(3)

