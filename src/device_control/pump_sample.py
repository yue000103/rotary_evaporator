import serial
import time
import logging

logger = logging.getLogger("PUMP")

class PumpSample:
    def __init__(self, port='COM3', baud_rate=9600, timeout=1, mock=False):
        """
        泵控制类，支持真实和 Mock 模式
        :param port: 串口号
        :param baud_rate: 波特率
        :param timeout: 超时时间
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        self.ID = 1
        self.SAMPLE_INLET_1 = "I"
        self.SAMPLE_OUTLET_3 = "O"
        self.SHORT_PORT = "I"
        self.DEFAULT_SPEED = {
            "port_1": {"suction": 4, "dispense": 3},
            "port_2": {"suction": 4, "dispense": 3},
            "port_3": {"suction": 4, "dispense": 3},
        }
        self.CALIBRATION_CURVE = {"k": 1, "b": 1}
        self.MAX_PULSE = 11000
        self.AIR_GAP_PULSE = 2000
        self.LIQUID_PULSE = 2000
        self.WAITING_TIME = 5000
        self.busy_flag = True

        if not self.mock:
            try:
                self.ser = serial.Serial(port, baud_rate, timeout=timeout)
                logger.info("UV检测器串口连接成功")
            except Exception as e:
                logger.error(f"无法连接到 UV 检测器串口: {e}")
                raise e
        else:
            logger.info("Mock 模式启用，不连接串口")

    def send_command(self, command: str) -> bytes:
        """
        发送命令并接收响应
        :param command: 要发送的命令
        :return: 设备的响应
        """
        formatted_command = f"/{self.ID}{command}R\r\n"
        logger.info(f"发送命令: {formatted_command.strip()}")

        if self.mock:
            response = f"[Mock Response] {command} OK".encode("utf-8")
            logger.info(f"Mock 模式返回: {response}")
            return response

        self.ser.write(formatted_command.encode("utf-8"))
        response = self.ser.readline()
        return response

    def initialization(self) -> bytes:
        """ 初始化泵 """
        return self.send_command("ZR")

    def ml_to_pulse(self, ml: float) -> int:
        """ 根据校准曲线计算所需的脉冲数 """
        return round(self.CALIBRATION_CURVE["k"] * ml + self.CALIBRATION_CURVE["b"])

    def inject(self, volume: float, in_port: int, out_port: int):
        """
        进行液体注射
        :param volume: 体积 (mL)
        :param in_port: 入口端口号
        :param out_port: 出口端口号
        """
        pulse = self.ml_to_pulse(volume)
        max_pulse_per_injection = self.MAX_PULSE - self.AIR_GAP_PULSE
        inject_cycles = pulse // max_pulse_per_injection
        last_time_pulse = pulse % max_pulse_per_injection

        in_speed = 1000
        out_speed = 1000

        if inject_cycles > 0:
            inject_cycles -= 1
            command = (
                f'{self.SAMPLE_INLET_1}gV{in_speed}A{self.MAX_PULSE}'
                f'M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0'
                f'{self.SAMPLE_INLET_1}G{inject_cycles}'
                f'V{in_speed}A{last_time_pulse + self.AIR_GAP_PULSE}M{self.WAITING_TIME}'
                f'{self.SAMPLE_OUTLET_3}V{out_speed}A{self.AIR_GAP_PULSE}M3000{self.SHORT_PORT}'
            )
        else:
            command = (
                f'{self.SAMPLE_INLET_1}V{in_speed}A{last_time_pulse + self.AIR_GAP_PULSE}'
                f'M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0M3000{self.SHORT_PORT}'
            )

        return self.send_command(command)

    def check_state(self):
        """ 查看泵的状态，并更新 busy_flag """
        re = self.send_command("Q")
        re_lst = list(re)

        if len(re_lst) < 4:
            logger.error("Unexpected response format")
            return

        status_code = re_lst[3]
        if status_code in range(64, 80):
            self.busy_flag = True
        elif status_code in range(96, 112):
            self.busy_flag = False
        else:
            logger.error(f"Unexpected status, received {re_lst}, flag is {status_code}")

        error_messages = {
            66: "Invalid command",
            67: "Invalid parameter in command",
            70: "EEPROM failed",
            71: "Pump was not initialized",
            73: "Pump overload, please check pressure",
            74: "Valve overload, please check valve",
            75: "Pump moving not allowed, please check valve position",
            76: "Unexpected error, please contact support",
            78: "A/D transmitter error, please contact support",
            79: "Command too long, please check command",
        }

        if status_code in error_messages:
            logger.error(f"[PUMP{self.ID}] {error_messages[status_code]}, received {re_lst}")

        if status_code in [71, 103]:  # 需要重新初始化
            self.initialization()
            self.sync()

    def sync(self):
        """ 等待泵空闲 """
        self.check_state()
        while self.busy_flag:
            time.sleep(0.5)
            self.check_state()

if __name__ == '__main__':
    ps = PumpSample(mock=True)  # 启用 Mock 模式
    response = ps.inject(5000, 1, 3)
    logger.info(f"Inject Response: {response}")
