import socket
import time
import logging

logger = logging.getLogger("PUMP")

class PumpSample:
    def  __init__(self, host='192.168.1.207', port=4196, baud_rate=9600, timeout=3, mock=False):
        """
        Pump control class supporting real and Mock modes
        :param port: Serial port number
        :param baud_rate: Baud rate
        :param timeout: Timeout value
        :param mock: Whether to enable Mock mode
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
        self.CALIBRATION_CURVE = {"k":2200, "b": 0}
        self.MAX_PULSE = 11000
        self.AIR_GAP_PULSE = 2000
        self.LIQUID_PULSE = 2000
        self.WAITING_TIME = 10000
        self.busy_flag = True
        self.host = host
        self.port = port

        if not self.mock:
            try:
                print(f"--------------{self.mock}------------------")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5)
                self.sock.connect((self.host, self.port))

                logger.info("Syringe pump serial connection successful")
                print(f"Syringe pump serial connection successful")

            except Exception as e:
                print(f"Unable to connect to syringe pump serial: {e}--")

                logger.error(f"Unable to connect to syringe pump serial: {e}")
                raise e
        else:
            logger.info("Mock mode enabled, no serial connection")

    def send_command(self, command: str) -> bytes:
        """
        Send command and receive response
        :param command: Command to send
        :return: Device response
        """
        formatted_command = f"/{self.ID}" + command + "R\r\n"

        logger.info(f"Sending command: {formatted_command.strip()}")

        if self.mock:
            response = f"[Mock Response] {command} OK".encode("utf-8")
            logger.info(f"Mock mode return: {response}")
            return response

        self.sock.sendall(formatted_command.encode("utf-8"))
        response = self._read_response()
        return response

    def _read_response(self, timeout=1):
        """Read response with timeout"""
        try:
            response = self.sock.recv(16)
            if not response:
                raise ConnectionError("Empty response")
            return response
        except socket.timeout:
            raise TimeoutError("Read timeout")

    def initialization(self):
        """Initialize pump"""
        self.send_command("Z")
        self.sync()
        self.send_command(self.SHORT_PORT)
        # return self.send_command("Z")

    def ml_to_pulse(self, ml: float) -> int:
        """Calculate required pulses based on calibration curve"""
        return round(self.CALIBRATION_CURVE["k"] * ml + self.CALIBRATION_CURVE["b"])

    def inject(self, volume: float, in_port: int, out_port: int):
        """
        Perform liquid injection
        :param volume: Volume (mL)
        :param in_port: Inlet port number
        :param out_port: Outlet port number
        """
        pulse = self.ml_to_pulse(volume)
        max_pulse_per_injection = self.MAX_PULSE - self.AIR_GAP_PULSE
        inject_cycles = pulse // max_pulse_per_injection
        last_time_pulse = pulse % max_pulse_per_injection

        in_speed = 1000
        out_speed = 1000

        if inject_cycles > 0:
            # inject_cycles -= 1
            command = (
            f'{self.SAMPLE_INLET_1}gV{in_speed}A{self.MAX_PULSE}'
            f'M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0M{self.WAITING_TIME}'
            f'{self.SAMPLE_INLET_1}G{inject_cycles}'
            f'V{in_speed}A{last_time_pulse + self.AIR_GAP_PULSE}M{self.WAITING_TIME}'
            f'{self.SAMPLE_OUTLET_3}V{out_speed}A{self.AIR_GAP_PULSE}M{self.WAITING_TIME}{self.SHORT_PORT}'
            )
        else:
            command = (
                f'{self.SAMPLE_INLET_1}V{in_speed}A{last_time_pulse + self.AIR_GAP_PULSE}'
                f'M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0M{self.WAITING_TIME}{self.SHORT_PORT}'
            )


        return self.send_command(command)

    def wash(self, volume: float):
        """
        Perform liquid washing
        :param volume: Volume (mL)
        """
        pulse = self.ml_to_pulse(volume)
        max_pulse_per_injection = self.MAX_PULSE - self.AIR_GAP_PULSE
        inject_cycles = pulse // max_pulse_per_injection
        last_time_pulse = pulse % max_pulse_per_injection

        in_speed = 1000
        out_speed = 1000

        if inject_cycles > 0:
            # inject_cycles -= 1
            command = (
            f'gV{in_speed}A{self.MAX_PULSE}'
            f'M{self.WAITING_TIME}V{out_speed}A0M{self.WAITING_TIME}'
            f'G{inject_cycles}'
            f'V{in_speed}A{last_time_pulse + self.AIR_GAP_PULSE}M{self.WAITING_TIME}'
            f'{self.SAMPLE_OUTLET_3}V{out_speed}A{self.AIR_GAP_PULSE}M{self.WAITING_TIME}{self.SHORT_PORT}'
            )
        else:
            command = (
                f'V{in_speed}A{last_time_pulse + self.AIR_GAP_PULSE}'
                f'M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0M{self.WAITING_TIME}{self.SHORT_PORT}'
            )


        return self.send_command(command)

    def check_state(self):
        """ 查看泵的状态，并更新 busy_flag """
        re = self.send_command("Q")
        re_lst = list(re)
        # print("re_lst",re_lst)

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
        if self.mock:
            return
        self.check_state()
        while self.busy_flag:
            time.sleep(0.5)
            self.check_state()
        self.send_command('I')
        time.sleep(1)

if __name__ == '__main__':
    ps = PumpSample(mock=False)  # 启用 Mock 模式
    # response = ps.inject(2, 1, 3)
    # print(f"Inject Response: {response}")
    # ps.sync()


    ps.send_command('V3000IA11000O')
    input('輸入enter繼續')

    t = 300
    v = int(11000/t)

    ps.send_command(f'V{v}A0')
    # ps.inject(1, 1, 3)
    # re = ps.initialization()
    # print("re",re)
    # ps.check_state()