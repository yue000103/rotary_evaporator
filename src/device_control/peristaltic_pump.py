import logging
import time

from src.com_control.PLC_com import PLCConnection
from src.uilt.logs_control.setup import device_control_logger


class PeristalticPump:
    def __init__(self, mock=False):
        """
        蠕动泵控制类，基于 Modbus 通信
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        self.plc = PLCConnection(mock=mock)

        # 定义寄存器地址
        self.REG_START_START = 300 # 泵启动
        self.REG_START_STOP = 301  # 泵停 (bool)
        self.REG_SPEED = 300  # 速度 (int, RPM)
        self.REG_VOLUME = 305  # 体积 (real, mL)
        self.PUMP_FINISH = 310
        self.WASHING_LIQUID_START = 320
        self.WASHING_LIQUID_STOP = 330
        self.WASTE_LIQUID_START = 321
        self.WASTE_LIQUID_STOP = 331


    def start_pump(self):
        """ 启动蠕动泵 """

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
    def stop_pump(self):
        """ 停止蠕动泵 """
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

if __name__ == '__main__':
    pump = PeristalticPump(mock=False)  # 启用 Mock 模式测试
    # pump.set_speed(1200)  # 设定转速

    pump.start_waste_liquid()  # 启动泵
    # pump.set_volume(500)  # 设定液体体积
    # pump.stop_pump()  # 停止泵
    #
    # pump.close()  # 关闭连接
