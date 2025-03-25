from src.uilt.logs_control.setup import com_logger
import time
from opentrons import protocol_api


class OpentronsCom:
    """
        Opentrons 设备通信控制
        """

    def __init__(self, mock=False):
        """
        初始化 Opentrons 连接
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        if not self.mock:
            self.protocol_context = self._initialize_opentrons()
        else:
            self.protocol_context = None
        com_logger.info("OpentronsConnection initialized.")

    def _initialize_opentrons(self):
        """初始化 Opentrons 设备"""
        com_logger.info("Initializing real Opentrons device...")
        return protocol_api.ProtocolContext

    def send_command(self, command):
        """发送命令"""
        if self.mock:
            com_logger.info(f"[Mock Mode] Sent: {command}")
            return f"[Mock Response] {command} {time.strftime('%H:%M:%S', time.localtime())}"

        com_logger.info(f"Executing command: {command}")
        # 这里可以执行一些实际的设备命令，例如 protocol_context.move()
        return "Command executed successfully"

    def close(self):
        """关闭连接"""
        com_logger.info("Closing Opentrons connection")