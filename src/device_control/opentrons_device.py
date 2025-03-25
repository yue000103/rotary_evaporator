from src.uilt.logs_control.setup import device_control_logger
from src.com_control.opentrons_com import OpentronsCom

class OpentronsDevice:
    """
    Opentrons 设备操作
    """
    def __init__(self, mock=False):
        """
        初始化设备
        :param mock: 是否启用 Mock 模式
        """
        self.connection = OpentronsCom(mock)

    def pick_up_tip(self):
        """取样品小瓶"""
        command = "PICK_UP_TIP"
        device_control_logger.info(f"Sending command: {command}")
        return self.connection.send_command(command)

    def transfer_liquid(self, from_well, to_well, volume):
        """执行液体转移"""
        command = f"TRANSFER {volume}µL FROM {from_well} TO {to_well}"
        device_control_logger.info(f"Sending command: {command}")
        return self.connection.send_command(command)

    def drop_tip(self):
        """丢弃吸头"""
        command = "DROP_TIP"
        device_control_logger.info(f"Sending command: {command}")
        return self.connection.send_command(command)

    def close(self):
        """关闭连接"""
        device_control_logger.info("Closing OpentronsDevice")
        self.connection.close()