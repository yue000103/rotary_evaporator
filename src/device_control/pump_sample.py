"""
注射泵控制模块

提供了对注射泵设备的完整控制接口，支持液体注射、清洗等操作。
基于 Socket 通信协议，支持 Mock 模式用于测试。
"""

import socket
import time
import logging
from enum import Enum, IntEnum
from typing import Optional, Dict, Tuple, Callable
from dataclasses import dataclass
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger("PUMP")


class PumpPort(str, Enum):
    """泵端口定义"""
    SAMPLE_INLET_1 = "I"      # 样品入口 1
    SAMPLE_OUTLET_3 = "O"     # 样品出口 3
    SHORT_PORT = "I"          # 短端口


class PumpStatus(IntEnum):
    """泵状态码定义"""
    # 忙碌状态范围: 64-79
    BUSY_MIN = 64
    BUSY_MAX = 79

    # 空闲状态范围: 96-111
    IDLE_MIN = 96
    IDLE_MAX = 111

    # 错误状态码
    ERROR_INVALID_COMMAND = 66
    ERROR_INVALID_PARAMETER = 67
    ERROR_EEPROM_FAILED = 70
    ERROR_NOT_INITIALIZED = 71
    ERROR_PUMP_OVERLOAD = 73
    ERROR_VALVE_OVERLOAD = 74
    ERROR_PUMP_NOT_ALLOWED = 75
    ERROR_UNEXPECTED = 76
    ERROR_AD_TRANSMITTER = 78
    ERROR_COMMAND_TOO_LONG = 79

    # 需要重新初始化的状态码
    NEED_REINIT_1 = 71
    NEED_REINIT_2 = 103


@dataclass
class CalibrationCurve:
    """校准曲线参数"""
    k: float = 2200.0  # 斜率
    b: float = 0.0     # 截距

    def ml_to_pulse(self, ml: float) -> int:
        """将毫升转换为脉冲数"""
        return round(self.k * ml + self.b)


@dataclass
class PumpConfig:
    """泵配置参数"""
    host: str = '192.168.1.207'
    port: int = 4196
    timeout: int = 5
    pump_id: int = 1

    # 泵运行参数
    max_pulse: int = 11000
    air_gap_pulse: int = 2000
    liquid_pulse: int = 2000
    waiting_time: int = 10000

    # 速度配置
    default_speed: Dict[str, Dict[str, int]] = None

    # 校准曲线
    calibration: CalibrationCurve = None

    def __post_init__(self):
        if self.default_speed is None:
            self.default_speed = {
                "port_1": {"suction": 4, "dispense": 3},
                "port_2": {"suction": 4, "dispense": 3},
                "port_3": {"suction": 4, "dispense": 3},
            }
        if self.calibration is None:
            self.calibration = CalibrationCurve()


def require_connection(func: Callable) -> Callable:
    """装饰器：确保在执行操作前已建立连接"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.mock and not self._is_connected():
            raise ConnectionError("泵未连接，请先建立连接")
        return func(self, *args, **kwargs)
    return wrapper


class PumpSample:
    """
    注射泵控制类

    支持液体注射、清洗等操作，提供完整的泵控制接口。
    基于 Socket 通信，支持 Mock 模式用于开发测试。

    使用示例:
        # 使用上下文管理器
        with PumpSample(host='192.168.1.207', port=4196) as pump:
            pump.initialization()
            pump.inject(volume=2.0, in_port=1, out_port=3)

        # 手动管理连接
        pump = PumpSample(mock=False)
        pump.connect()
        pump.initialization()
        pump.inject(2.0, 1, 3)
        pump.close()
    """

    # 错误信息映射
    ERROR_MESSAGES = {
        PumpStatus.ERROR_INVALID_COMMAND: "无效命令",
        PumpStatus.ERROR_INVALID_PARAMETER: "命令参数无效",
        PumpStatus.ERROR_EEPROM_FAILED: "EEPROM 失败",
        PumpStatus.ERROR_NOT_INITIALIZED: "泵未初始化",
        PumpStatus.ERROR_PUMP_OVERLOAD: "泵过载，请检查压力",
        PumpStatus.ERROR_VALVE_OVERLOAD: "阀门过载，请检查阀门",
        PumpStatus.ERROR_PUMP_NOT_ALLOWED: "泵移动不允许，请检查阀门位置",
        PumpStatus.ERROR_UNEXPECTED: "意外错误，请联系技术支持",
        PumpStatus.ERROR_AD_TRANSMITTER: "A/D 传输器错误，请联系技术支持",
        PumpStatus.ERROR_COMMAND_TOO_LONG: "命令过长，请检查命令",
    }

    def __init__(self, host: str = '192.168.1.207', port: int = 4196,
                 timeout: int = 5, mock: bool = False,
                 config: Optional[PumpConfig] = None):
        """
        初始化注射泵控制器

        :param host: 泵的 IP 地址
        :param port: 通信端口
        :param timeout: 通信超时时间（秒）
        :param mock: 是否启用 Mock 模式（用于测试）
        :param config: 泵配置对象，如果为 None 则使用默认配置
        """
        self.mock = mock
        self.config = config or PumpConfig(host=host, port=port, timeout=timeout)
        self.sock: Optional[socket.socket] = None
        self._busy_flag = True
        self._connected = False

        if not self.mock:
            self.connect()
        else:
            logger.info("Mock 模式启用，不连接设备")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def connect(self) -> None:
        """建立与注射泵的连接"""
        if self.mock or self._connected:
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.config.timeout)
            self.sock.connect((self.config.host, self.config.port))
            self._connected = True
            logger.info(f"注射泵连接成功 [{self.config.host}:{self.config.port}]")
        except Exception as e:
            logger.error(f"无法连接到注射泵: {e}")
            raise ConnectionError(f"注射泵连接失败: {e}") from e

    def close(self) -> None:
        """关闭连接"""
        if self.sock and self._connected:
            try:
                self.sock.close()
                self._connected = False
                logger.info("注射泵连接已关闭")
            except Exception as e:
                logger.warning(f"关闭连接时出错: {e}")

    def _is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self.sock is not None

    @require_connection
    def send_command(self, command: str) -> bytes:
        """
        发送命令并接收响应

        :param command: 要发送的命令字符串
        :return: 设备的响应（字节形式）
        :raises ConnectionError: 连接错误
        :raises TimeoutError: 响应超时
        """
        formatted_command = f"/{self.config.pump_id}{command}R\r\n"
        logger.info(f"发送命令: {formatted_command.strip()}")

        if self.mock:
            response = f"[Mock Response] {command} OK".encode("utf-8")
            logger.info(f"Mock 模式返回: {response.decode('utf-8', errors='ignore')}")
            return response

        try:
            self.sock.sendall(formatted_command.encode("utf-8"))
            response = self._read_response()
            logger.debug(f"收到响应: {response}")
            return response
        except socket.timeout:
            raise TimeoutError("命令响应超时")
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            raise

    def _read_response(self, buffer_size: int = 16) -> bytes:
        """
        读取响应数据

        :param buffer_size: 缓冲区大小
        :return: 响应字节数据
        :raises ConnectionError: 接收到空响应
        :raises TimeoutError: 读取超时
        """
        try:
            response = self.sock.recv(buffer_size)
            if not response:
                raise ConnectionError("接收到空响应")
            return response
        except socket.timeout:
            raise TimeoutError("读取响应超时")

    @require_connection
    def initialization(self) -> None:
        """初始化泵到默认状态"""
        logger.info("开始初始化注射泵")
        self.send_command("Z")
        self.sync()
        self.send_command(PumpPort.SHORT_PORT.value)
        logger.info("注射泵初始化完成")

    def ml_to_pulse(self, ml: float) -> int:
        """
        根据校准曲线将体积转换为脉冲数

        :param ml: 液体体积（毫升）
        :return: 脉冲数
        """
        return self.config.calibration.ml_to_pulse(ml)

    def _build_injection_command(self, pulse: int, in_speed: int = 1000,
                                 out_speed: int = 1000,
                                 include_ports: bool = True) -> str:
        """
        构建注射命令字符串

        :param pulse: 总脉冲数
        :param in_speed: 吸入速度
        :param out_speed: 排出速度
        :param include_ports: 是否包含端口切换命令
        :return: 命令字符串
        """
        max_pulse_per_injection = self.config.max_pulse - self.config.air_gap_pulse
        inject_cycles = pulse // max_pulse_per_injection
        last_time_pulse = pulse % max_pulse_per_injection

        inlet_port = PumpPort.SAMPLE_INLET_1.value if include_ports else ""
        outlet_port = PumpPort.SAMPLE_OUTLET_3.value
        short_port = PumpPort.SHORT_PORT.value
        waiting = self.config.waiting_time

        if inject_cycles > 0:
            command = (
                f'{inlet_port}gV{in_speed}A{self.config.max_pulse}'
                f'M{waiting}{outlet_port}V{out_speed}A0M{waiting}'
                f'{inlet_port}G{inject_cycles}'
                f'V{in_speed}A{last_time_pulse + self.config.air_gap_pulse}M{waiting}'
                f'{outlet_port}V{out_speed}A{self.config.air_gap_pulse}M{waiting}{short_port}'
            )
        else:
            command = (
                f'{inlet_port}V{in_speed}A{last_time_pulse + self.config.air_gap_pulse}'
                f'M{waiting}{outlet_port}V{out_speed}A0M{waiting}{short_port}'
            )

        return command

    @require_connection
    def inject(self, volume: float, in_port: int = 1, out_port: int = 3,
               in_speed: int = 1000, out_speed: int = 1000) -> bytes:
        """
        执行液体注射操作

        :param volume: 注射体积（毫升）
        :param in_port: 入口端口号（当前未使用，保留用于扩展）
        :param out_port: 出口端口号（当前未使用，保留用于扩展）
        :param in_speed: 吸入速度（脉冲/秒）
        :param out_speed: 排出速度（脉冲/秒）
        :return: 设备响应
        """
        logger.info(f"开始注射操作: 体积={volume}ml, 入口={in_port}, 出口={out_port}")

        pulse = self.ml_to_pulse(volume)
        command = self._build_injection_command(pulse, in_speed, out_speed, include_ports=True)

        response = self.send_command(command)
        logger.info(f"注射操作完成")
        return response

    @require_connection
    def wash(self, volume: float, in_speed: int = 1000, out_speed: int = 1000) -> bytes:
        """
        执行清洗操作

        :param volume: 清洗液体积（毫升）
        :param in_speed: 吸入速度（脉冲/秒）
        :param out_speed: 排出速度（脉冲/秒）
        :return: 设备响应
        """
        logger.info(f"开始清洗操作: 体积={volume}ml")

        pulse = self.ml_to_pulse(volume)
        command = self._build_injection_command(pulse, in_speed, out_speed, include_ports=False)

        response = self.send_command(command)
        logger.info(f"清洗操作完成")
        return response

    @require_connection
    def check_state(self) -> Tuple[bool, Optional[str]]:
        """
        检查泵的当前状态

        :return: (是否忙碌, 错误消息) 元组
        """
        response = self.send_command("Q")
        response_list = list(response)

        if len(response_list) < 4:
            error_msg = f"状态响应格式异常: {response_list}"
            logger.error(error_msg)
            return self._busy_flag, error_msg

        status_code = response_list[3]

        # 更新忙碌状态
        if PumpStatus.BUSY_MIN <= status_code <= PumpStatus.BUSY_MAX:
            self._busy_flag = True
        elif PumpStatus.IDLE_MIN <= status_code <= PumpStatus.IDLE_MAX:
            self._busy_flag = False
        else:
            logger.warning(f"未知的状态码: {status_code}, 响应: {response_list}")

        # 检查错误状态
        error_message = None
        if status_code in self.ERROR_MESSAGES:
            error_message = self.ERROR_MESSAGES[status_code]
            logger.error(f"[PUMP{self.config.pump_id}] {error_message}, 状态码: {status_code}")

        # 需要重新初始化
        if status_code in [PumpStatus.NEED_REINIT_1, PumpStatus.NEED_REINIT_2]:
            logger.warning("检测到需要重新初始化，正在执行...")
            self.initialization()
            self.sync()

        return self._busy_flag, error_message

    @require_connection
    def sync(self, check_interval: float = 0.5) -> None:
        """
        等待泵操作完成（同步等待）

        :param check_interval: 状态检查间隔（秒）
        """
        if self.mock:
            logger.debug("Mock 模式下跳过同步等待")
            return

        logger.debug("开始同步等待泵空闲")
        self.check_state()

        while self._busy_flag:
            time.sleep(check_interval)
            is_busy, error = self.check_state()
            if error:
                logger.warning(f"同步等待中检测到错误: {error}")

        self.send_command(PumpPort.SAMPLE_INLET_1.value)
        time.sleep(1)
        logger.debug("泵已空闲，同步完成")

    @property
    def is_busy(self) -> bool:
        """获取泵是否忙碌"""
        return self._busy_flag

    @property
    def is_connected(self) -> bool:
        """获取连接状态"""
        return self._is_connected()

    def set_calibration(self, k: float, b: float = 0.0) -> None:
        """
        设置校准曲线参数

        :param k: 斜率
        :param b: 截距
        """
        self.config.calibration = CalibrationCurve(k=k, b=b)
        logger.info(f"校准曲线已更新: k={k}, b={b}")

    def __repr__(self) -> str:
        """对象字符串表示"""
        status = "已连接" if self._connected else "未连接"
        mode = "Mock" if self.mock else "实际"
        return (f"PumpSample(host={self.config.host}, port={self.config.port}, "
                f"模式={mode}, 状态={status})")


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 示例1: 使用上下文管理器（推荐）
    with PumpSample(mock=True) as pump:
        pump.initialization()
        pump.inject(volume=2.0, in_port=1, out_port=3)
        pump.wash(volume=1.0)

    # 示例2: 手动管理连接
    # pump = PumpSample(host='192.168.1.207', port=4196, mock=False)
    # try:
    #     pump.initialization()
    #     pump.inject(2.0, 1, 3)
    #     pump.sync()
    # finally:
    #     pump.close()

    # 示例3: 自定义配置
    # config = PumpConfig(
    #     host='192.168.1.207',
    #     port=4196,
    #     max_pulse=12000,
    #     air_gap_pulse=2500
    # )
    # pump = PumpSample(config=config, mock=False)
    # pump.set_calibration(k=2500, b=10)
    # pump.inject(3.0, 1, 3)