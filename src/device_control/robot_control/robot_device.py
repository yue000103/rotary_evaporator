from src.com_control.robot_com import RobotConnection
from src.uilt.logs_control.setup import device_control_logger
import threading
import time

class RobotController:
    def __init__(self, mock=False):
        """
        机器人设备控制
        :param mock: 是否启用 Mock 模式
        """
        self.connection = RobotConnection(mock)
        self.monitor_thread = None
        self.monitor_active = False  # 控制线程运行的标志

    def start_connection_monitor(self):
        """启动一个后台线程持续监控连接"""
        if self.monitor_active:
            return  # 避免重复启动
        self.monitor_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_connection, daemon=False)
        self.monitor_thread.start()

    def _monitor_connection(self):
        """线程执行的内部方法"""
        while self.monitor_active:
            try:
                self.ensure_connection()
                time.sleep(1)  # 每秒检查一次，减少CPU占用
            except Exception as e:
                device_control_logger.error(f"Connection monitor error: {e}")
                break

    def stop_connection_monitor(self):
        """停止监控线程"""
        self.monitor_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join()

    def ensure_connection(self):
        """ 确保客户端已连接 """
        # if not self.connection.client_socket:
        #     device_control_logger.info("Waiting for robot client connection...")
        #     self.connection.accept_client()
        pass

    def move_forward(self, distance):
        """ 控制机器人前进 """
        self.ensure_connection()
        command = f"MOVE FORWARD {distance}"
        device_control_logger.info(f"Sending command: {command}")
        response = self.connection.send_command(command)
        return response

    def rotate(self, angle):
        """ 控制机器人旋转 """
        self.ensure_connection()
        command = f"ROTATE {angle}"
        device_control_logger.info(f"Sending command: {command}")
        response = self.connection.send_command(command)
        return response

    def stop(self):
        """ 停止机器人 """
        self.ensure_connection()
        command = "STOP"
        device_control_logger.info("Sending command: STOP")
        response = self.connection.send_command(command)
        return response

    def start(self):
        """ 停止机器人 """
        # self.ensure_connection()

        command = 'ok'
        device_control_logger.info("Sending command: ok")
        response = self.connection.send_command(command)


        return response

    def get_status(self):
        """ 获取机器人状态 """
        self.ensure_connection()
        command = "STATUS"
        device_control_logger.info("Sending command: STATUS")
        response = self.connection.send_command(command)
        return response

    def trasfer_flask(self, from_flask_id, to_flask_id):
        """ 放置试剂瓶，从 from_flask_id 移动到 to_flask_id """

        self.ensure_connection()
        command = f'trasfer_flask({from_flask_id},{to_flask_id})'
        # print("command:", command)
        device_control_logger.info(f"Sending command: {command}")
        response = self.connection.send_command(command)
        # response = ""
        return response

    def start_liquid_transfer(self,bottle_id):
        """ 机器人抓取两个进样针 """
        command = f'liquid_transfer_start({bottle_id})'
        device_control_logger.info(f"Sending command: {command}")
        response = self.connection.send_command(command)
        return response

    def start_spray(self):
        """ 机器人抓取喷淋头，对准大瓶 """
        self.ensure_connection()
        command = "START_SPRAY"
        device_control_logger.info("Sending command: START_SPRAY")
        response = self.connection.send_command(command)
        return response

    def liquid_transfer_finish(self):
        """ 机器人放回进样针 """
        self.ensure_connection()
        command = "liquid_transfer_finish"
        device_control_logger.info("Sending command: liquid_transfer_finish")
        response = self.connection.send_command(command)
        return response

    def close(self):
        """ 关闭连接 """
        device_control_logger.info("Closing RobotController connection")
        self.connection.close()

    def send_ok(self):
        self.ensure_connection()
        command = 'ok'
        device_control_logger.info("Sending command: liquid_transfer_finish")
        response = self.connection.send_command(command)
        return response

    def down_collect_needle(self):
        command = 'ok'
        device_control_logger.info("Sending command: liquid_transfer_finish")
        response = self.connection.send_command(command)
        return response

    def rise_collect_needle(self):
        command = 'ok'
        device_control_logger.info("Sending command: liquid_transfer_finish")
        response = self.connection.send_command(command)
        return response

    def robot_change_gripper(self):
        command = 'ok'
        device_control_logger.info("Sending command: liquid_transfer_finish")
        response = self.connection.send_command(command)
        return response

    def inject_sample_finish(self):
        command = 'ok'
        device_control_logger.info("Sending command: inject_sample_finish")
        response = self.connection.send_command(command)
        return response



# 使用示例
if __name__ == "__main__":
    controller = RobotController(mock=False)  # 启用模拟模式
    controller.start_connection_monitor()
    controller.start()
    # time.sleep(50)
    # controller.start_liquid_transfer(1)
    # time.sleep(50)
    # controller.liquid_transfer_finish()

    # print("机器人放试剂瓶：", controller.trasfer_flask(7,17))
    # controller.start_liquid_transfer(1)
    # print("机器人旋蒸上样（1000mL大瓶）：", controller.trasfer_flask(1,1))
    #
    # print("机器人取样品小瓶（机器人）200mL 小瓶，放到转移工位：", controller.trasfer_flask(1,1))
    #
    # print("机器人清洗大瓶：", controller.start_liquid_transfer())
    #
    # print("液体转移完成：", controller.liquid_transfer_finish())
    # controller.close()
