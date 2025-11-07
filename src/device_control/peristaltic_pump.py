import logging
import time
from enum import Enum
from typing import Optional, Dict, Tuple

from src.com_control import plc
from src.util.logs_control.setup import device_control_logger


class PumpType(Enum):
    """蠕动泵类型枚举"""
    TRANSFER = "transfer"      # 转移液体泵
    WASHING = "washing"        # 清洗液泵（清洗进样针）
    WASTE = "waste"           # 废液泵（排放废弃液体）


class PeristalticPump:
    """
    蠕动泵控制类，基于 Modbus 通信
    管理三个独立的蠕动泵：
    1. 转移液体泵：用于样品转移等操作
    2. 清洗液泵：用于清洗进样针
    3. 废液泵：用于旋蒸时排放废弃液体
    """

    # 默认超时和轮询间隔配置
    DEFAULT_TIMEOUT = 300  # 默认超时时间（秒）
    POLL_INTERVAL = 2      # 轮询间隔（秒）

    def __init__(self, mock=False, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化蠕动泵控制器
        :param mock: 是否启用 Mock 模式
        :param timeout: 操作超时时间（秒），默认 300 秒
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock
        self.timeout = timeout
        self.logger = device_control_logger

        # 定义寄存器地址映射
        # 每个泵都有：启动寄存器、停止寄存器、完成标志寄存器
        self._pump_registers: Dict[PumpType, Dict[str, int]] = {
            PumpType.TRANSFER: {
                'start': 300,      # 转移液体泵启动
                'stop': 301,       # 转移液体泵停止
                'finish': 310      # 转移液体泵完成标志
            },
            PumpType.WASHING: {
                'start': 320,      # 清洗液泵启动
                'stop': 321,       # 清洗液泵停止
                'finish': 330      # 清洗液泵完成标志
            },
            PumpType.WASTE: {
                'start': 340,      # 废液泵启动
                'stop': 341,       # 废液泵停止
                'finish': 350      # 废液泵完成标志
            }
        }

        # 通用控制寄存器（可选，用于高级控制）
        self.REG_SPEED = 302        # 速度 (int, RPM)
        self.REG_VOLUME = 305       # 体积 (real, mL)

        # 向后兼容的寄存器别名
        self.REG_START_START = self._pump_registers[PumpType.TRANSFER]['start']
        self.REG_START_STOP = self._pump_registers[PumpType.TRANSFER]['stop']
        self.PUMP_FINISH = self._pump_registers[PumpType.TRANSFER]['finish']
        self.WASHING_LIQUID_START = self._pump_registers[PumpType.WASHING]['start']
        self.WASHING_LIQUID_STOP = self._pump_registers[PumpType.WASHING]['finish']
        self.WASTE_LIQUID_START = self._pump_registers[PumpType.WASTE]['start']
        self.WASTE_LIQUID_STOP = self._pump_registers[PumpType.WASTE]['finish']  # 向后兼容别名
        self.WASTE_LIQUID_FINISH = self._pump_registers[PumpType.WASTE]['finish']


    def _write_pulse_signal(self, register: int, description: str) -> None:
        """
        向指定寄存器写入脉冲信号（高-低-高）
        :param register: 寄存器地址
        :param description: 操作描述（用于日志）
        """
        try:
            self.plc.write_coil(register, True)
            time.sleep(1)
            self.plc.write_coil(register, False)
            self.logger.info(f"{description} - 脉冲信号已发送到寄存器 {register}")
        except Exception as e:
            self.logger.error(f"{description} - 写入寄存器 {register} 失败: {e}")
            raise

    def _wait_for_completion(self, status_register: int, operation_name: str,
                            timeout: Optional[int] = None) -> bool:
        """
        等待操作完成的通用方法
        :param status_register: 状态寄存器地址
        :param operation_name: 操作名称（用于日志）
        :param timeout: 超时时间（秒），如果为 None 则使用默认超时
        :return: 是否成功完成
        :raises TimeoutError: 操作超时
        """
        timeout = timeout or self.timeout
        start_time = time.time()

        self.logger.info(f"{operation_name} - 开始等待完成，超时时间: {timeout}秒")

        while True:
            elapsed_time = time.time() - start_time

            # 检查超时
            if elapsed_time >= timeout:
                error_msg = f"{operation_name} - 操作超时（{timeout}秒）"
                self.logger.error(error_msg)
                raise TimeoutError(error_msg)

            try:
                # 读取完成状态
                done = self.plc.read_coils(status_register)[0]
                if done:
                    self.logger.info(f"{operation_name} - 操作完成，耗时: {elapsed_time:.2f}秒")
                    return True

            except Exception as e:
                self.logger.warning(f"{operation_name} - 读取状态失败: {e}，继续重试...")

            time.sleep(self.POLL_INTERVAL)

    # ==================== 统一泵控制接口 ====================

    def _get_pump_name(self, pump_type: PumpType) -> str:
        """获取泵的中文名称"""
        names = {
            PumpType.TRANSFER: "转移液体泵",
            PumpType.WASHING: "清洗液泵",
            PumpType.WASTE: "废液泵"
        }
        return names.get(pump_type, "未知泵")

    def start_pump_by_type(self, pump_type: PumpType,
                          wait_for_completion: bool = True,
                          timeout: Optional[int] = None) -> bool:
        """
        统一的泵启动接口（推荐使用）
        :param pump_type: 泵类型（PumpType 枚举）
        :param wait_for_completion: 是否等待操作完成
        :param timeout: 超时时间（秒），如果为 None 则使用默认超时
        :return: 是否成功完成
        """
        pump_name = self._get_pump_name(pump_type)
        registers = self._pump_registers[pump_type]

        self.logger.info(f"启动{pump_name}")

        try:
            self._write_pulse_signal(registers['start'], f"{pump_name}启动")
            time.sleep(2)  # 等待泵启动

            if wait_for_completion:
                return self._wait_for_completion(
                    registers['finish'],
                    f"{pump_name}操作",
                    timeout
                )
            return True

        except Exception as e:
            self.logger.error(f"{pump_name}启动失败: {e}")
            raise

    def stop_pump_by_type(self, pump_type: PumpType) -> None:
        """
        统一的泵停止接口（推荐使用）
        :param pump_type: 泵类型（PumpType 枚举）
        """
        pump_name = self._get_pump_name(pump_type)
        registers = self._pump_registers[pump_type]

        self.logger.info(f"停止{pump_name}")
        try:
            self._write_pulse_signal(registers['stop'], f"{pump_name}停止")
        except Exception as e:
            self.logger.error(f"{pump_name}停止失败: {e}")
            raise

    def is_pump_running(self, pump_type: PumpType) -> bool:
        """
        查询泵是否正在运行（通过检查完成标志的反向状态）
        :param pump_type: 泵类型
        :return: True 表示正在运行，False 表示已停止
        """
        pump_name = self._get_pump_name(pump_type)
        registers = self._pump_registers[pump_type]

        try:
            finished = self.plc.read_coils(registers['finish'])[0]
            is_running = not finished
            self.logger.debug(f"{pump_name}运行状态: {'运行中' if is_running else '已停止'}")
            return is_running
        except Exception as e:
            self.logger.error(f"读取{pump_name}状态失败: {e}")
            raise

    def get_all_pump_status(self) -> Dict[PumpType, bool]:
        """
        获取所有泵的运行状态
        :return: 字典，键为泵类型，值为是否正在运行
        """
        status = {}
        for pump_type in PumpType:
            try:
                status[pump_type] = self.is_pump_running(pump_type)
            except Exception as e:
                self.logger.warning(f"读取{self._get_pump_name(pump_type)}状态失败: {e}")
                status[pump_type] = None
        return status

    # ==================== 转移液体泵控制方法 ====================

    def start_transfer_pump(self, wait_for_completion: bool = True,
                           timeout: Optional[int] = None) -> bool:
        """
        启动转移液体泵（用于样品转移等操作）
        :param wait_for_completion: 是否等待操作完成
        :param timeout: 超时时间（秒），如果为 None 则使用默认超时
        :return: 是否成功完成
        """
        return self.start_pump_by_type(PumpType.TRANSFER, wait_for_completion, timeout)

    def stop_transfer_pump(self) -> None:
        """停止转移液体泵"""
        self.stop_pump_by_type(PumpType.TRANSFER)

    # ==================== 清洗液泵控制方法 ====================

    def start_washing_liquid_pump(self, wait_for_completion: bool = True,
                                   timeout: Optional[int] = None) -> bool:
        """
        启动清洗液泵（用于清洗进样针）
        :param wait_for_completion: 是否等待操作完成
        :param timeout: 超时时间（秒），如果为 None 则使用默认超时
        :return: 是否成功完成
        """
        return self.start_pump_by_type(PumpType.WASHING, wait_for_completion, timeout)

    def stop_washing_liquid_pump(self) -> None:
        """停止清洗液泵"""
        self.stop_pump_by_type(PumpType.WASHING)

    # ==================== 废液泵控制方法 ====================

    def start_waste_liquid_pump(self, wait_for_completion: bool = True,
                                 timeout: Optional[int] = None) -> bool:
        """
        启动废液泵（用于旋蒸时排放废弃液体）
        :param wait_for_completion: 是否等待操作完成
        :param timeout: 超时时间（秒），如果为 None 则使用默认超时
        :return: 是否成功完成
        """
        return self.start_pump_by_type(PumpType.WASTE, wait_for_completion, timeout)

    def stop_waste_liquid_pump(self) -> None:
        """停止废液泵"""
        self.stop_pump_by_type(PumpType.WASTE)

    # ==================== 通用控制方法（兼容旧代码）====================

    def start_pump(self, wait_for_completion: bool = True,
                   timeout: Optional[int] = None) -> bool:
        """
        启动蠕动泵（通用方法）
        :param wait_for_completion: 是否等待操作完成
        :param timeout: 超时时间（秒）
        :return: 是否成功完成
        """
        self.logger.info("启动蠕动泵（通用）")

        try:
            self.plc.write_coil(self.REG_START_START, False)
            time.sleep(1)
            self.plc.write_coil(self.REG_START_START, True)
            time.sleep(2)

            if wait_for_completion:
                return self._wait_for_completion(
                    self.PUMP_FINISH,
                    "蠕动泵传输",
                    timeout
                )
            return True

        except Exception as e:
            self.logger.error(f"蠕动泵启动失败: {e}")
            raise

    def stop_pump(self) -> None:
        """
        停止蠕动泵（通用方法）
        """
        self.logger.info("停止蠕动泵（通用）")
        try:
            self.plc.write_coil(self.REG_START_STOP, False)
            time.sleep(1)
            self.plc.write_coil(self.REG_START_STOP, True)
            time.sleep(1)
            self.plc.write_coil(self.REG_START_STOP, False)
            self.logger.info("蠕动泵已停止")
        except Exception as e:
            self.logger.error(f"蠕动泵停止失败: {e}")
            raise

    # ==================== 向后兼容的别名方法 ====================

    def start_washing_liquid(self, wait_for_completion: bool = True) -> bool:
        """向后兼容的方法，调用新方法"""
        return self.start_washing_liquid_pump(wait_for_completion)

    def start_waste_liquid(self, wait_for_completion: bool = True) -> bool:
        """向后兼容的方法，调用新方法"""
        return self.start_waste_liquid_pump(wait_for_completion)

if __name__ == '__main__':
    # 创建蠕动泵控制器实例
    pump = PeristalticPump(mock=True, timeout=300)

    print("=" * 60)
    print("蠕动泵控制器示例")
    print("=" * 60)

    # ========== 方式1：使用统一接口（推荐） ==========
    print("\n【方式1：使用统一接口（推荐）】")

    # 启动转移液体泵
    # pump.start_pump_by_type(PumpType.TRANSFER, wait_for_completion=True)
    # pump.stop_pump_by_type(PumpType.TRANSFER)

    # 启动清洗液泵
    # pump.start_pump_by_type(PumpType.WASHING, wait_for_completion=True, timeout=180)

    # 启动废液泵
    # pump.start_pump_by_type(PumpType.WASTE, wait_for_completion=False)

    # 查询所有泵的状态
    # status = pump.get_all_pump_status()
    # for pump_type, is_running in status.items():
    #     print(f"{pump_type.value}: {'运行中' if is_running else '已停止'}")

    # ========== 方式2：使用专用方法 ==========
    print("\n【方式2：使用专用方法】")

    # 转移液体泵
    # pump.start_transfer_pump(wait_for_completion=True)
    # pump.stop_transfer_pump()

    # 清洗液泵（用于清洗进样针）
    # pump.start_washing_liquid_pump(wait_for_completion=True)
    # pump.stop_washing_liquid_pump()

    # 废液泵（用于排放废弃液体）
    # pump.start_waste_liquid_pump(wait_for_completion=True, timeout=180)
    # pump.stop_waste_liquid_pump()

    # ========== 方式3：向后兼容的旧方法 ==========
    print("\n【方式3：向后兼容的旧方法】")

    # 通用泵控制（映射到转移液体泵）
    # pump.start_pump(wait_for_completion=True)
    # pump.stop_pump()

    # 旧的别名方法
    # pump.start_washing_liquid(wait_for_completion=True)
    # pump.start_waste_liquid(wait_for_completion=True)

    # ========== 高级功能 ==========
    print("\n【高级功能：状态查询】")

    # 查询单个泵状态
    # is_running = pump.is_pump_running(PumpType.TRANSFER)
    # print(f"转移液体泵状态: {'运行中' if is_running else '已停止'}")

    # 查询所有泵状态
    # all_status = pump.get_all_pump_status()
    # for pump_type, running in all_status.items():
    #     status_text = "运行中" if running else "已停止" if running is not None else "状态未知"
    #     print(f"  {pump._get_pump_name(pump_type)}: {status_text}")

    print("\n蠕动泵控制器初始化完成")
