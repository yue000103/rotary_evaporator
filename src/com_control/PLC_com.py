import logging
from pymodbus.client import ModbusTcpClient
from src.uilt.yaml_control.setup import get_base_url
from src.uilt.logs_control.setup import com_logger

class PLCConnection:
    def __init__(self, mock=False):
        """
        PLC 通信控制
        :param mock: 是否启用 Mock 模式
        """
        self.host = get_base_url("plc_com")
        self.port = 502  # Modbus TCP 默认端口
        self.mock = mock
        self.client = None

        if not self.mock:
            self._connect()

        com_logger.info(f"PLCConnection initialized on {self.host}:{self.port}")

    def _connect(self):
        """ 初始化 Modbus TCP 连接 """
        self.client = ModbusTcpClient(self.host, port=self.port)
        if self.client.connect():
            print("Connected to PLC Server")
            com_logger.info("Connected to PLC Server")
        else:
            com_logger.error("Failed to connect to PLC Server")

    def read_holding_registers(self, address, count):
        """ 读取保持寄存器的值 """
        if self.mock:
            com_logger.info(f"[Mock Mode] Reading {count} holding registers from address {address}")
            return [i for i in range(count)]

        try:
            result = self.client.read_holding_registers(address, count)
            if not result.isError():
                com_logger.info(f"Read {count} holding registers from address {address}: {result.registers}")
                return result.registers
            else:
                com_logger.error(f"Error reading holding registers: {result}")
                return None
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return None

    def write_single_register(self, address, value):
        """ 写入单个保持寄存器的值 """
        if self.mock:
            com_logger.info(f"[Mock Mode] Writing value {value} to holding register at address {address}")
            return True

        try:
            result = self.client.write_register(address, value)
            if not result.isError():
                com_logger.info(f"Successfully wrote value {value} to holding register at address {address}")
                return True
            else:
                com_logger.error(f"Error writing single register: {result}")
                return False
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return False

    def write_registers(self, address, values):
        """ 写入多个保持寄存器 """
        if self.mock:
            com_logger.info(f"[Mock Mode] Writing values {values} to holding registers starting at address {address}")
            return True

        try:
            result = self.client.write_registers(address, values)
            if not result.isError():
                com_logger.info(f"Successfully wrote values {values} to holding registers starting at address {address}")
                return True
            else:
                com_logger.error(f"Error writing multiple registers: {result}")
                return False
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return False

    def write_coil(self, address, value):
        """ 写入单个线圈 (布尔值) """
        if self.mock:
            com_logger.info(f"[Mock Mode] Writing coil {value} to address {address}")
            return True

        try:
            result = self.client.write_coil(address, value)
            if not result.isError():
                com_logger.info(f"Successfully wrote coil {value} to address {address}")
                return True
            else:
                com_logger.error(f"Error writing coil: {result}")
                return False
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return False

    def read_coils(self, address, count=1):
        """ 读取线圈 (布尔值) """
        if self.mock:
            mock_values = [True] * count
            com_logger.info(f"[Mock Mode] Reading {count} coils from address {address}: {mock_values}")
            return mock_values

        try:
            result = self.client.read_coils(address, count)
            if not result.isError():
                com_logger.info(f"Read {count} coils from address {address}: {result.bits}")
                return result.bits
            else:
                com_logger.error(f"Error reading coils: {result}")
                return None
        except Exception as e:
            com_logger.error(f"Error in communication: {e}")
            return None

    def close(self):
        """ 关闭连接 """
        if self.client:
            self.client.close()
            com_logger.info("PLC Connection closed")

if __name__ == '__main__':
    # 创建 PLC 连接实例
    plc = PLCConnection(mock=False)

    # 读取保持寄存器
    # registers = plc.read_holding_registers(address=0, count=5)
    # if registers:
    #     print(f"Read registers: {registers}")
    #
    # # 写入单个保持寄存器
    # write_success = plc.write_single_register(address=1, value=100)
    # if write_success:
    #     print("Successfully wrote value to register")
    #
    # # 写入多个寄存器
    # write_multiple_success = plc.write_registers(address=2, values=[10, 20, 30])
    # if write_multiple_success:
    #     print("Successfully wrote multiple values to registers")
    #
    # # 写入单个线圈 (bool)
    # write_coil_success = plc.write_coil(address=5, value=True)
    # if write_coil_success:
    #     print("Successfully wrote coil value")
    #
    # # 读取线圈状态
    # coils = plc.read_coils(address=5, count=3)
    # if coils is not None:
    #     print(f"Read coil values: {coils}")
    #
    # # 关闭连接
    # plc.close()
