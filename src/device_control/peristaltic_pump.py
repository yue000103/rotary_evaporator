import logging
import time

from src.com_control import plc
from src.uilt.logs_control.setup import device_control_logger


class PeristalticPump:
    def __init__(self, mock=False):
        """
        Peristaltic pump control class based on Modbus communication
        :param mock: Whether to enable Mock mode
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock
        self.REG_START_START = 300
        self.REG_START_STOP = 301
        self.PUMP_FINISH = 310
        self.WASHING_LIQUID_START = 320
        self.WASHING_LIQUID_STOP = 330
        self.WASTE_LIQUID_START = 321
        self.WASTE_LIQUID_STOP = 331

    def start_pump(self):
        """Start peristaltic pump"""

        self.plc.write_coil(self.REG_START_START, False)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_START, True)
        # time.sleep(1)
        # self.plc.write_coil(self.REG_START_START, False)
        time.sleep(2)
        self.transfer_finish_async()

    def transfer_finish_async(self):
        while True:
            done = self.plc.read_coils(self.PUMP_FINISH)[0]
            if done:
                return True
            time.sleep(2)
    def stop_pump(self):
        """Stop peristaltic pump"""
        self.plc.write_coil(self.REG_START_STOP, False)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_STOP, True)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_STOP, False)

    def start_washing_liquid(self):
        self.plc.write_coil(self.WASHING_LIQUID_START, True)
        time.sleep(1)
        self.plc.write_coil(self.WASHING_LIQUID_START, False)
        time.sleep(2)
        self.washing_liquid_finish_async()

    def washing_liquid_finish_async(self):
        while True:
            done = self.plc.read_coils(self.WASHING_LIQUID_STOP)[0]
            if done:
                return True
            time.sleep(2)

    def start_waste_liquid(self):
        self.plc.write_coil(self.WASTE_LIQUID_START, True)
        time.sleep(1)
        self.plc.write_coil(self.WASTE_LIQUID_START, False)
        time.sleep(2)
        # self.waste_liquid_finish_async()

    def waste_liquid_finish_async(self):
        while True:
            done = self.plc.read_coils(self.WASTE_LIQUID_STOP)[0]
            if done:
                return True
            time.sleep(2)

if __name__ == '__main__':
    pump = PeristalticPump(mock=False)
