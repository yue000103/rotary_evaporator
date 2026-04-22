import logging
from pymodbus.client import ModbusTcpClient
from src.uilt.yaml_control.setup import get_base_url
from src.uilt.logs_control.setup import com_logger
import struct
import threading




class PLCConnection:

    @staticmethod
    def synchronized(func):
        def wrapper(self, *args, **kwargs):
            with self.lock:
                return func(self, *args, **kwargs)
        return wrapper  # 需要返回 wrapper 函数

    @staticmethod
    def retry(max_attempts=3):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                attempts = 0
                while attempts < max_attempts:
                    try:
                        return func(self, *args, **kwargs)
                    except Exception as e:
                        attempts += 1
                        if attempts == max_attempts:
                            com_logger.error(f"Final attempt failed for {func.__name__}: {e}")
                            raise
                        com_logger.warning(f"Attempt {attempts} failed for {func.__name__}: {e}. Retrying...")
                return None
            return wrapper
        return decorator

    def __init__(self):
        """
        PLC communication control
        :param mock: Whether to enable Mock mode
        """
        self.host = get_base_url("plc_com")
        self.port = 502
        self.mock = False
        self.client:ModbusTcpClient|None = None
        self.lock = threading.Lock()

        if not self.mock:
            print("Connecting to PLC controller...")
            self._connect()

        com_logger.info(f"PLCConnection initialized on {self.host}:{self.port}")

    def _connect(self):
        """Initialize Modbus TCP connection"""
        self.client = ModbusTcpClient(self.host, port=self.port)
        if self.client.connect():
            print("Connected to PLC Server")
            com_logger.info("Connected to PLC Server")
        else:
            com_logger.error("Failed to connect to PLC Server")

    @synchronized
    def read_holding_registers(self, address, count):
        """Read holding register values"""
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

    @synchronized
    def write_single_register(self, address, value):
        """Write single holding register value"""
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

    @synchronized
    def write_registers(self, address, values):
        """Write multiple holding registers"""
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

    @synchronized
    def write_coil(self, address, value):
        """Write single coil (boolean)"""
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

    @synchronized
    def read_coils(self, address, count=1):
        """Read coils (boolean)"""
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
        """Close connection"""
        if self.client:
            self.client.close()
            com_logger.info("PLC Connection closed")

    def float_to_registers(self, value):
        # 使用 IEEE 754 将浮点数转换为 4 字节
        packed = struct.pack(">f", value)
        # 将 4 字节转换为两个 16 位整数
        registers = struct.unpack(">HH", packed)
        return registers

    def split_dint(self,value):
        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF
        return high, low

    @synchronized
    def write_dint_register(self, address, value):
        high, low = self.split_dint(value)
        registers = [low, high]

        if self.mock:
            mock_values = registers
            com_logger.info(f"[Mock Mode] Writing {registers} from address {address}: {mock_values}")
            return mock_values

        response = self.client.write_registers(address=address, values=registers, unit=1)

        if response.isError():
            print("Write failed:", response)
        else:
            print("Write successful!")

if __name__ == '__main__':
    plc = PLCConnection(mock=False)
