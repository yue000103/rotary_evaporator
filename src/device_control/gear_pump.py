import logging
import time

from src.com_control import plc
from src.util.logs_control.setup import device_control_logger


class GearPump:
    def __init__(self, mock=False):
        """
        蠕动泵控制类，基于 Modbus 通信
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock  # 设置 PLC 通信是否为 Mock 模式

        # 定义寄存器地址
        self.REG_START_START = 306
        self.REG_START_STOP = 306  # 泵启停 (bool)
        self.REG_TIME_S = 102  # 泵启停 (bool)
        self.PUMP_FINISH = 316



    def start_pump(self,time_s):

        #写时间
        # self.plc.write_coil(self.REG_START_START, False)
        # time.sleep(1)
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




    def stop_pump(self):
        self.plc.write_coil(self.REG_START_STOP, False)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_STOP, True)
        time.sleep(1)
        self.plc.write_coil(self.REG_START_STOP, False)






if __name__ == '__main__':
    pump = GearPump(mock=False)  # 启用 Mock 模式测试

    pump.start_pump(3)  # 启动泵

    # pump.stop_pump()  # 停止泵

