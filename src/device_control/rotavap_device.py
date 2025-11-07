"""
旋蒸设备控制模块

提供旋转蒸发仪的完整控制接口，包括：
- 加热、冷却、真空控制
- 旋转、升降控制
- 自动高度设置
- 废液处理
- 真空阈值监控
"""

import time
import json
import logging
from enum import Enum, IntEnum
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict

from src.com_control.xuanzheng_com import ConnectionController
from src.com_control import plc

logger = logging.getLogger("XUANZHENG")


class FlaskSize(IntEnum):
    """烧瓶尺寸枚举"""
    SMALL = 1   # 小烧瓶（50ml, 100ml, 500ml）
    LARGE = 2   # 大烧瓶（1000ml）


class ProgramType(str, Enum):
    """程序类型枚举"""
    AUTO_DEST = "AutoDest"  # 自动蒸馏


class VolumeHeight(IntEnum):
    """不同体积对应的高度设置"""
    VOLUME_1000ML = 1050
    VOLUME_500ML = 1150
    VOLUME_100ML = 1400
    VOLUME_50ML = 1417
    VOLUME_0ML = 0


@dataclass
class HeatingConfig:
    """加热配置"""
    set: float                    # 设定温度
    running: bool = False         # 是否运行


@dataclass
class CoolingConfig:
    """冷却配置"""
    set: float                    # 设定温度
    running: bool = False         # 是否运行


@dataclass
class VacuumConfig:
    """真空配置"""
    set: float                         # 设定真空度
    vacuumValveOpen: bool = False      # 真空阀开关
    aerateValveOpen: bool = False      # 充气阀开关
    aerateValvePulse: bool = False     # 充气阀脉冲


@dataclass
class RotationConfig:
    """旋转配置"""
    set: float                    # 设定转速
    running: bool = True          # 是否运行


@dataclass
class LiftConfig:
    """升降配置"""
    set: float                    # 设定位置


@dataclass
class ProgramConfig:
    """程序配置"""
    type: str = ProgramType.AUTO_DEST.value  # 程序类型
    endVacuum: float = 0                     # 结束真空度
    flaskSize: int = FlaskSize.LARGE.value   # 烧瓶尺寸


@dataclass
class DeviceStatus:
    """设备状态"""
    running: bool = False         # 是否运行
    vacuum_actual: float = 0.0    # 当前真空度
    heating_actual: float = 0.0   # 当前加热温度
    cooling_actual: float = 0.0   # 当前冷却温度
    rotation_actual: float = 0.0  # 当前转速


class RotavapController:
    """
    旋转蒸发仪控制器

    提供完整的旋蒸设备控制接口，支持加热、冷却、真空、旋转等功能。
    集成 PLC 控制用于自动高度调节和废液处理。

    使用示例:
        # 基本使用
        controller = XuanzhengController(mock=False)
        controller.set_height(1000)  # 设置1000ml烧瓶高度
        controller.run_evaporation()  # 开始蒸发
        controller.xuanzheng_sync(timeout_min=30)  # 同步等待完成

        # 真空控制
        controller.vacuum_until_below_threshold(threshold=400)
        controller.drain_until_above_threshold(threshold=900)
    """

    # PLC 寄存器地址定义
    HEIGHT_ADDRESS = 502           # 高度设置地址
    AUTO_SET = 500                 # 自动设置地址
    AUTO_FINISH = 501              # 自动完成标志
    WASTE_LIQUID = 323             # 废液启动地址
    WASTE_LIQUID_FINISH = 333      # 废液完成标志

    # 默认参数
    DEFAULT_VACUUM_SET = 150       # 默认真空设定值
    DEFAULT_LIFT_SET = 0           # 默认升降位置
    DEFAULT_POLL_INTERVAL = 2      # 默认轮询间隔（秒）
    DEFAULT_SYNC_TIMEOUT = 120     # 默认同步超时（分钟）

    # 体积到高度的映射
    VOLUME_HEIGHT_MAP = {
        1000: (VolumeHeight.VOLUME_1000ML, FlaskSize.LARGE),
        500: (VolumeHeight.VOLUME_500ML, FlaskSize.SMALL),
        100: (VolumeHeight.VOLUME_100ML, FlaskSize.SMALL),
        50: (VolumeHeight.VOLUME_50ML, FlaskSize.SMALL),
        0: (VolumeHeight.VOLUME_0ML, FlaskSize.SMALL),
    }

    def __init__(self, mock: bool = False):
        """
        初始化旋蒸控制器

        :param mock: 是否启用 Mock 模式（用于测试）
        """
        self.mock = mock
        self.connection = ConnectionController(mock)
        self.plc = plc
        self.plc.mock = mock
        self.logger = logger

        if mock:
            self.logger.info("旋蒸控制器启用 Mock 模式")
        else:
            self.logger.info("旋蒸控制器初始化完成")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def close(self) -> None:
        """关闭连接"""
        try:
            self.connection.close()
            self.logger.info("旋蒸控制器连接已关闭")
        except Exception as e:
            self.logger.warning(f"关闭连接时出错: {e}")

    # ==================== API 通信方法 ====================

    def get_info(self) -> Dict[str, Any]:
        """
        获取设备信息

        :return: 设备信息字典
        """
        try:
            response = self.connection.send_request("/api/v1/info", method='GET')
            self.logger.debug(f"获取设备信息: {response}")
            return self._parse_response(response)
        except Exception as e:
            self.logger.error(f"获取设备信息失败: {e}")
            raise

    def get_process(self) -> Dict[str, Any]:
        """
        获取当前工艺过程状态

        :return: 过程状态字典
        """
        try:
            response = self.connection.send_request("/api/v1/process", method='GET')
            return self._parse_response(response)
        except Exception as e:
            self.logger.error(f"获取过程状态失败: {e}")
            raise

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """
        解析 API 响应

        :param response: 原始响应
        :return: 解析后的字典
        """
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            if not response.strip():
                self.logger.warning("收到空响应")
                return {}
            try:
                return json.loads(response)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON 解析失败: {e}, 原始数据: {response}")
                return {}
        else:
            self.logger.warning(f"未知的响应类型: {type(response)}")
            return {}

    def get_device_status(self) -> DeviceStatus:
        """
        获取设备当前状态

        :return: DeviceStatus 对象
        """
        process_data = self.get_process()

        return DeviceStatus(
            running=process_data.get("globalStatus", {}).get("running", False),
            vacuum_actual=process_data.get("vacuum", {}).get("act", 0.0),
            heating_actual=process_data.get("heating", {}).get("act", 0.0),
            cooling_actual=process_data.get("cooling", {}).get("act", 0.0),
            rotation_actual=process_data.get("rotation", {}).get("act", 0.0),
        )

    # ==================== 设备参数控制 ====================

    def change_device_parameters(
        self,
        heating: Optional[HeatingConfig] = None,
        cooling: Optional[CoolingConfig] = None,
        vacuum: Optional[VacuumConfig] = None,
        rotation: Optional[RotationConfig] = None,
        lift: Optional[LiftConfig] = None,
        running: Optional[bool] = None,
        program: Optional[ProgramConfig] = None
    ) -> Dict[str, Any]:
        """
        更改设备参数

        :param heating: 加热配置
        :param cooling: 冷却配置
        :param vacuum: 真空配置
        :param rotation: 旋转配置
        :param lift: 升降配置
        :param running: 运行状态
        :param program: 程序配置
        :return: 服务器响应
        """
        data = {}

        if heating is not None:
            data["heating"] = asdict(heating)

        if cooling is not None:
            data["cooling"] = asdict(cooling)

        if vacuum is not None:
            data["vacuum"] = asdict(vacuum)

        if rotation is not None:
            data["rotation"] = asdict(rotation)

        if lift is not None:
            data["lift"] = asdict(lift)

        if running is not None:
            data["globalStatus"] = {"running": running}

        if program is not None:
            data["program"] = asdict(program)

        try:
            response = self.connection.send_request("/api/v1/process", method='PUT', data=data)
            self.logger.info(f"更改设备参数成功: {list(data.keys())}")
            return self._parse_response(response)
        except Exception as e:
            self.logger.error(f"更改设备参数失败: {e}")
            raise

    # ==================== 高度控制 ====================

    def set_height(self, volume: int) -> None:
        """
        根据烧瓶体积设置高度

        :param volume: 烧瓶体积（支持: 1000, 500, 100, 50, 0）
        :raises ValueError: 不支持的体积值
        """
        if volume not in self.VOLUME_HEIGHT_MAP:
            raise ValueError(
                f"不支持的体积值: {volume}ml, "
                f"支持的值: {list(self.VOLUME_HEIGHT_MAP.keys())}"
            )

        height, flask_size = self.VOLUME_HEIGHT_MAP[volume]

        self.logger.info(f"设置高度: 体积={volume}ml, 高度={height}, 烧瓶尺寸={flask_size}")

        try:
            # 写入高度寄存器
            self.plc.write_single_register(self.HEIGHT_ADDRESS, height)

            # 设置烧瓶尺寸（除了归零位置）
            if volume > 0:
                program = ProgramConfig(
                    type=ProgramType.AUTO_DEST.value,
                    flaskSize=flask_size
                )
                self.change_device_parameters(program=program)

            time.sleep(1)

            # 启动自动设置
            self.plc.write_coil(self.AUTO_SET, True)
            time.sleep(3)

            # 等待完成
            self._wait_height_finish()

            # 复位自动设置标志
            time.sleep(1)
            self.plc.write_coil(self.AUTO_SET, False)

            self.logger.info(f"高度设置完成: {volume}ml")

        except Exception as e:
            self.logger.error(f"设置高度失败: {e}")
            raise

    def _wait_height_finish(self, timeout: int = 120) -> bool:
        """
        等待高度设置完成

        :param timeout: 超时时间（秒）
        :return: 是否成功完成
        :raises TimeoutError: 操作超时
        """
        start_time = time.time()
        self.logger.debug("等待高度设置完成")

        while True:
            if time.time() - start_time > timeout:
                error_msg = f"高度设置超时（{timeout}秒）"
                self.logger.error(error_msg)
                raise TimeoutError(error_msg)

            try:
                done = self.plc.read_coils(self.AUTO_FINISH, 1)[0]
                if done:
                    self.logger.debug("高度设置完成")
                    return True
            except Exception as e:
                self.logger.warning(f"读取完成状态失败: {e}")

            time.sleep(2)

    # ==================== 废液控制 ====================

    def start_waste_liquid(self, wait_for_completion: bool = False,
                          timeout: int = 60) -> bool:
        """
        启动废液排放

        :param wait_for_completion: 是否等待完成
        :param timeout: 超时时间（秒）
        :return: 是否成功
        """
        self.logger.info("启动废液排放")

        try:
            # 发送脉冲信号
            self.plc.write_coil(self.WASTE_LIQUID, True)
            time.sleep(1)
            self.plc.write_coil(self.WASTE_LIQUID, False)
            time.sleep(2)

            if wait_for_completion:
                return self._wait_waste_finish(timeout)

            return True

        except Exception as e:
            self.logger.error(f"废液启动失败: {e}")
            return False

    def _wait_waste_finish(self, timeout: int = 60) -> bool:
        """
        等待废液排放完成

        :param timeout: 超时时间（秒）
        :return: 是否成功完成
        :raises TimeoutError: 操作超时
        """
        start_time = time.time()
        self.logger.debug("等待废液排放完成")

        while True:
            if time.time() - start_time > timeout:
                error_msg = f"废液排放超时（{timeout}秒）"
                self.logger.error(error_msg)
                raise TimeoutError(error_msg)

            try:
                done = self.plc.read_coils(self.WASTE_LIQUID_FINISH)[0]
                if done:
                    self.logger.info("废液排放完成")
                    return True
            except Exception as e:
                self.logger.warning(f"读取废液完成状态失败: {e}")

            time.sleep(1)

    # ==================== 蒸发过程控制 ====================

    def run_evaporation(self, delay: int = 10) -> Dict[str, Any]:
        """
        启动蒸发过程

        :param delay: 启动后延迟时间（秒）
        :return: 服务器响应
        """
        self.logger.info("启动蒸发过程")
        response = self.change_device_parameters(running=True)
        time.sleep(delay)
        return response

    def stop_evaporation(self) -> Dict[str, Any]:
        """
        停止蒸发过程

        :return: 服务器响应
        """
        self.logger.info("停止蒸发过程")
        return self.change_device_parameters(running=False)

    def xuanzheng_sync(self, timeout_min: int = DEFAULT_SYNC_TIMEOUT,
                       poll_interval: int = DEFAULT_POLL_INTERVAL) -> bool:
        """
        同步等待旋蒸过程完成

        等待设备从未运行 -> 运行中 -> 运行结束的完整周期

        :param timeout_min: 超时时间（分钟）
        :param poll_interval: 轮询间隔（秒）
        :return: 是否成功完成
        """
        has_started = False
        timeout = timeout_min * 60
        start_time = time.time()

        self.logger.info(f"开始同步等待旋蒸过程，超时: {timeout_min}分钟")

        try:
            while True:
                elapsed = time.time() - start_time

                # 检查超时
                if elapsed > timeout:
                    self.logger.warning(f"同步等待超时（{timeout_min}分钟），停止蒸发")
                    self.stop_evaporation()
                    return False

                # 获取当前状态
                status = self.get_device_status()
                self.logger.debug(
                    f"当前状态: running={status.running}, "
                    f"vacuum={status.vacuum_actual:.1f}mbar"
                )

                # 状态机逻辑
                if status.running:
                    if not has_started:
                        self.logger.info("检测到设备开始运行")
                        has_started = True
                elif has_started:
                    self.logger.info("检测到运行结束，同步完成")
                    return True
                else:
                    self.logger.debug("等待设备启动...")

                time.sleep(poll_interval)

        except Exception as e:
            self.logger.error(f"同步等待过程中发生异常: {e}")
            return False

    # ==================== 真空控制 ====================

    def run_vacuum(self) -> Dict[str, Any]:
        """
        启动真空泵

        :return: 服务器响应
        """
        self.logger.info("启动真空泵")
        vacuum_config = VacuumConfig(
            set=self.DEFAULT_VACUUM_SET,
            vacuumValveOpen=True,
            aerateValveOpen=False
        )
        lift_config = LiftConfig(set=self.DEFAULT_LIFT_SET)

        return self.change_device_parameters(
            vacuum=vacuum_config,
            lift=lift_config
        )

    def stop_vacuum(self) -> Dict[str, Any]:
        """
        停止真空泵

        :return: 服务器响应
        """
        self.logger.info("停止真空泵")
        vacuum_config = VacuumConfig(
            set=self.DEFAULT_VACUUM_SET,
            vacuumValveOpen=False,
            aerateValveOpen=False
        )
        lift_config = LiftConfig(set=self.DEFAULT_LIFT_SET)

        return self.change_device_parameters(
            vacuum=vacuum_config,
            lift=lift_config
        )

    def drain_valve_open(self, duration: int = 5) -> Dict[str, Any]:
        """
        打开排气阀

        :param duration: 打开持续时间（秒）
        :return: 服务器响应
        """
        self.logger.info(f"打开排气阀，持续 {duration} 秒")
        vacuum_config = VacuumConfig(
            set=self.DEFAULT_VACUUM_SET,
            vacuumValveOpen=False,
            aerateValveOpen=True,
            aerateValvePulse=False
        )

        response = self.change_device_parameters(vacuum=vacuum_config)
        time.sleep(duration)
        return response

    def vacuum_until_below_threshold(self, threshold: float = 400,
                                     poll_interval: int = 1) -> bool:
        """
        抽真空直到低于阈值

        :param threshold: 真空度阈值（mbar）
        :param poll_interval: 轮询间隔（秒）
        :return: 是否成功
        """
        if self.mock:
            self.logger.info(f"Mock 模式: 真空值已低于 {threshold}mbar")
            return True

        self.logger.info(f"开始抽真空，目标: < {threshold}mbar")
        self.run_vacuum()

        try:
            while True:
                status = self.get_device_status()
                vacuum_actual = status.vacuum_actual

                self.logger.debug(f"当前真空值: {vacuum_actual:.1f}mbar")

                if vacuum_actual < threshold:
                    self.logger.info(f"真空值已低于 {threshold}mbar，停止抽真空")
                    self.stop_vacuum()
                    return True

                time.sleep(poll_interval)

        except Exception as e:
            self.logger.error(f"抽真空过程出错: {e}")
            self.stop_vacuum()
            return False

    def drain_until_above_threshold(self, threshold: float = 900,
                                    poll_interval: int = 1,
                                    wait_after: int = 5) -> bool:
        """
        排气直到高于阈值

        :param threshold: 真空度阈值（mbar）
        :param poll_interval: 轮询间隔（秒）
        :param wait_after: 达到阈值后等待时间（秒）
        :return: 是否成功
        """
        if self.mock:
            self.logger.info(f"Mock 模式: 真空值已高于 {threshold}mbar")
            return True

        self.logger.info(f"开始排气，目标: > {threshold}mbar")
        self.drain_valve_open(duration=0)  # 不自动等待

        try:
            while True:
                status = self.get_device_status()
                vacuum_actual = status.vacuum_actual

                self.logger.debug(f"当前真空值: {vacuum_actual:.1f}mbar")

                if vacuum_actual > threshold:
                    self.logger.info(
                        f"真空值已高于 {threshold}mbar，等待 {wait_after} 秒"
                    )
                    time.sleep(wait_after)
                    return True

                time.sleep(poll_interval)

        except Exception as e:
            self.logger.error(f"排气过程出错: {e}")
            return False

    def __repr__(self) -> str:
        """对象字符串表示"""
        mode = "Mock" if self.mock else "实际"
        return f"XuanzhengController(模式={mode})"


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 示例1: 使用上下文管理器
    with RotavapController(mock=True) as controller:
        # 设置高度
        controller.set_height(1000)

        # 启动蒸发
        controller.run_evaporation()

        # 同步等待完成
        controller.xuanzheng_sync(timeout_min=30)

        # 归零
        controller.set_height(0)

    # 示例2: 真空控制
    # controller = XuanzhengController(mock=False)
    # controller.vacuum_until_below_threshold(threshold=400)
    # controller.drain_until_above_threshold(threshold=900)
    # controller.start_waste_liquid(wait_for_completion=True)
    # controller.close()

    # 示例3: 手动控制
    # controller = XuanzhengController(mock=False)
    #
    # # 设置参数
    # heating = HeatingConfig(set=60, running=True)
    # vacuum = VacuumConfig(set=150, vacuumValveOpen=True)
    # controller.change_device_parameters(heating=heating, vacuum=vacuum)
    #
    # # 获取状态
    # status = controller.get_device_status()
    # print(f"当前状态: {status}")
    #
    # controller.close()
