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
        self.REG_START_START = 99
        self.REG_START_STOP = 99  # 泵启停 (bool)
        self.REG_SPEED = 99  # 速度 (int, RPM)
        self.REG_VOLUME = 99  # 体积 (real, mL)

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



    def set_speed(self, speed: int):
        """ 设置泵的转速 (RPM) """
        if not (0 < speed <= 300):  # 假设最大转速为 5000 RPM
            device_control_logger.error("转速超出范围！有效范围: 1 - 5000 RPM")
            return
        success = self.plc.write_single_register(self.REG_SPEED, speed)
        if success:
            device_control_logger.info(f"蠕动泵速度设定为 {speed} RPM")
        else:
            device_control_logger.error("设置速度失败")

    def set_volume(self, volume_ml: float):
        """ 设置泵的液体体积 (mL) """
        if volume_ml <= 0:
            device_control_logger.error("液体体积必须大于 0")
            return
        volume_int = int(volume_ml * 100)  # 假设 PLC 以 0.01 mL 为单位存储
        success = self.plc.write_single_register(self.REG_VOLUME, volume_int)
        if success:
            device_control_logger.info(f"蠕动泵设定液体体积为 {volume_ml} mL")
        else:
            device_control_logger.error("设置液体体积失败")

    def close(self):
        """ 关闭 PLC 连接 """
        self.plc.close()
        device_control_logger.info("蠕动泵连接已关闭")


if __name__ == '__main__':
    pump = PeristalticPump(mock=True)  # 启用 Mock 模式测试

    pump.start_pump()  # 启动泵
    pump.set_speed(1200)  # 设定转速
    pump.set_volume(500)  # 设定液体体积
    pump.stop_pump()  # 停止泵

    pump.close()  # 关闭连接
