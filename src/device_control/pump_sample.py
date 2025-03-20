import serial
import time
import logging

logger = logging.getLogger("PUMP")

class PumpSample:
    def __init__(self, port='COM3', baud_rate=9600, timeout=1):
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=timeout)
            print("UV检测器串口连接成功")
        except Exception as e:
            print(f"无法连接到UV检测器串口: {e}")
            raise e
        self.ID = 1
        self.SAMPLE_INLET_1 = "I"
        self.SAMPLE_OUTLET_3 = "O"
        # self.LIQUID_INLET_2 = "I"
        self.SHORT_PORT = "I"
        self.DEFAULT_SPEED = {
            "port_1": {
                 "suction": 4,
                 "dispense": 3
            },
            "port_2": {
                "suction": 4,
                "dispense": 3
            },
            "port_3": {
                "suction": 4,
                "dispense": 3
            },
        }
        self.CALIBRATION_CURVE = {
                "k": 1,
                "b": 1
        }
        self.MAX_PULSE = 11000
        self.AIR_GAP_PULSE = 2000
        self.LIQUID_PULSE = 2000
        self.WAITING_TIME = 5000

        self.busy_flag: bool = True


    def send_command(self, command:str) -> bytes:
        """
        发送命令并接收响应。

        :param command: 要发送的命令。
        :return: 设备的响应。
        """
        command = f"/{self.ID}" + command + "R\r\n"
        print(command)

        self.ser.write(command.encode('utf-8'))
        response = self.ser.readline()
        return response

    def initialization(self) -> bytes:
        """
        初始化泵，
        :return: 初始化返回值
        """
        re = self.send_command(
            "ZR"
        )
        return re

    def ml_to_pulse(self, ml: float) -> int:
        """
        根据校准曲线计算所需的脉冲数
        :param ml: 要计算的体积,以mL为单位
        :return: 脉冲数(int)
        """
        pulse = round(self.CALIBRATION_CURVE["k"] * ml + self.CALIBRATION_CURVE["b"])

        return pulse

    def inject(self,volume:float, in_port: int,out_port: int,):
        pulse = self.ml_to_pulse(volume)
        max_pulse_per_injection = (
                self.MAX_PULSE - self.AIR_GAP_PULSE
        )  # 每次最多打出的脉冲数
        inject_cycles = pulse // max_pulse_per_injection  # 循环的次数
        last_time_pulse = pulse % max_pulse_per_injection  # 最后一次打出的脉冲数


        # in_speed = round(
        #     self.DEFAULT_SPEED[f"port_{in_port}"]["suction"]
        #     * self.CALIBRATION_CURVE["k"]
        # )
        in_speed = 1000
        # out_speed = round(
        #     self.DEFAULT_SPEED[f"port_{out_port}"]["dispense"]
        #     * self.CALIBRATION_CURVE["k"]
        # )
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
        # 清洗注射器步骤
        # command += {
        #     f'{self.LIQUID_INLET_2}V{in_speed}A{self.LIQUID_PULSE}M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0'
        #     f'{self.LIQUID_INLET_2}V{in_speed}A{self.LIQUID_PULSE}M{self.WAITING_TIME}{self.SAMPLE_OUTLET_3}V{out_speed}A0'
        #     f'{self.SHORT_PORT}'
        # }
        re = self.send_command(command)

    def check_state(self):
        """
        查看泵的状态,并更新 busy_flag属性
        :return: None
        """
        re = self.send_command("Q")
        # print(re)
        re_lst = list(re)
        # print("re_lst-----------",re_lst)

        if re_lst[3] in range(64, 80):
            self.busy_flag = True
        elif re_lst[3] in range(96, 112):
            self.busy_flag = False
        else:
            logging.error(f"Unexpected status, received {re_lst}, flag is {re_lst[3]}")

        if re_lst[3] == 64 or re_lst[3] == 96:  # 无错误
            pass

        elif re_lst[3] == 65 or re_lst[3] == 97:  # 初始化中
            pass

        elif re_lst[3] == 66 or re_lst[3] == 98:  # 无效指令
            logger.error(f"[PUMP{self.ID}] Invalid command , received {re_lst}")

        elif re_lst[3] == 67 or re_lst[3] == 99:
            logger.error(f"[PUMP{self.ID}] Invalid parameter in command , received {re_lst}")

        elif re_lst[3] == 70 or re_lst[3] == 102:
            logger.error(f"[PUMP{self.ID}] EEPROM failed , received {re_lst}")

        elif re_lst[3] == 71 or re_lst[3] == 103:
            logger.error(f"[PUMP{self.ID}] pump was not initialized , received {re_lst}")
            self.initialization()
            self.sync()
            self.initialization_flag = True

        elif re_lst[3] == 73 or re_lst[3] == 105:
            logger.error(f"[PUMP{self.ID}] pump overload ,please check pressure, received {re_lst}")

        elif re_lst[3] == 74 or re_lst[3] == 106:
            logger.error(f"[PUMP{self.ID}] valve overload ,please check valve, received {re_lst}")

        elif re_lst[3] == 75 or re_lst[3] == 107:
            logger.error(f"[PUMP{self.ID}] pump moving not allowed ,please check valve position, received {re_lst}")

        elif re_lst[3] == 76 or re_lst[3] == 108:
            logger.error(f"[PUMP{self.ID}] unexpected error ,please contact RUNZE flied , received {re_lst}")

        elif re_lst[3] == 78 or re_lst[3] == 110:
            logger.error(f"[PUMP{self.ID}] A/D transmitter error  ,please contact RUNZE flied , received {re_lst}")

        elif re_lst[3] == 79 or re_lst[3] == 111:
            logger.error(f"[PUMP{self.ID}] command toooooo long!  ,please check command , received {re_lst}")

        else:
            logging.error(f"Unexpected status, received {re_lst}, flag is {re_lst[3]}")

    def sync(self):
        """
        同步指令,等待泵的
        :return:
        """
        self.check_state()
        while self.busy_flag:
            time.sleep(0.5)
            self.check_state()

if __name__ == '__main__':
    ps = PumpSample()
    ps.inject(5000,1,3)
    # ps.send_command("IV3000A5000M3000V1000A0")
    # ps.send_command("ZR")
    # ps.sync()