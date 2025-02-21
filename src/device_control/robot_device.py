from src.com_control.robot_com import RobotConnection
from src.uilt.logs_control import device_control_logger


class RobotController:
    def __init__(self, mock=False):
        """
        机器人设备控制
        :param host: 机器人服务器 IP
        :param port: 机器人服务器端口
        :param mock: 是否启用 Mock 模式
        """
        self.connection = RobotConnection(mock)

    def move_forward(self, distance):
        """ 控制机器人前进 """
        command = f"MOVE FORWARD {distance}"
        device_control_logger.info(f"Sending command: {command}")
        response = self.connection.send_command(command)
        device_control_logger.info(f"Response received: {response}")
        return response

    def rotate(self, angle):
        """ 控制机器人旋转 """
        command = f"ROTATE {angle}"
        device_control_logger.info(f"Sending command: {command}")
        response = self.connection.send_command(command)
        device_control_logger.info(f"Response received: {response}")
        return response

    def stop(self):
        """ 停止机器人 """
        command = "STOP"
        device_control_logger.info("Sending command: STOP")
        response = self.connection.send_command(command)
        device_control_logger.info(f"Response received: {response}")
        return response

    def get_status(self):
        """ 获取机器人状态 """
        command = "STATUS"
        device_control_logger.info("Sending command: STATUS")
        response = self.connection.send_command(command)
        device_control_logger.info(f"Response received: {response}")
        return response

    def close(self):
        """ 关闭连接 """
        device_control_logger.info("Closing RobotController connection")
        self.connection.close()


# 使用示例
if __name__ == "__main__":
    controller = RobotController(mock=True)  # 启用模拟模式
    print("状态信息：", controller.get_status())
    print("移动指令：", controller.move_forward(10))
    print("旋转指令：", controller.rotate(90))
    print("停止指令：", controller.stop())
    controller.close()
