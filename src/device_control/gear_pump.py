import time

from src.com_control import plc
from src.util.logs_control.setup import device_control_logger


class GearPump:
    """齿轮泵控制类，基于 Modbus/PLC 通信控制齿轮泵的启停和运行时间"""

    # 寄存器地址定义
    REG_PUMP_CONTROL = 306      # 泵启停控制寄存器 (bool)
    REG_PUMP_TIME_MS = 102      # 泵运行时间寄存器 (毫秒, DINT)
    REG_PUMP_FINISH = 316       # 泵运行完成状态寄存器 (bool)

    # 默认配置
    DEFAULT_POLL_INTERVAL = 1.0  # 轮询间隔（秒）
    DEFAULT_TIMEOUT = 300.0      # 默认超时时间（秒）

    def __init__(self, mock: bool = False, poll_interval: float = DEFAULT_POLL_INTERVAL):
        """
        初始化齿轮泵控制器

        :param mock: 是否启用 Mock 模式，用于测试
        :param poll_interval: 状态轮询间隔（秒），默认为 1.0 秒
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock
        self.poll_interval = poll_interval
        self.logger = device_control_logger

    def start_pump(self, duration_seconds: float, wait_for_completion: bool = True,
                   timeout: float = None) -> bool:
        """
        启动齿轮泵并运行指定时间

        :param duration_seconds: 泵运行时长（秒）
        :param wait_for_completion: 是否等待泵运行完成，默认为 True
        :param timeout: 等待超时时间（秒），默认使用 DEFAULT_TIMEOUT
        :return: 操作是否成功
        """
        try:
            if timeout is None:
                timeout = self.DEFAULT_TIMEOUT

            # 转换为毫秒
            duration_ms = int(duration_seconds * 1000)

            self.logger.info(f"启动齿轮泵，运行时长: {duration_seconds}秒 ({duration_ms}毫秒)")

            # 启动泵
            self.plc.write_coil(self.REG_PUMP_CONTROL, True)
            time.sleep(1)

            # 设置运行时间
            self.plc.write_dint_register(self.REG_PUMP_TIME_MS, duration_ms)
            self.logger.info("泵运行参数设置完成")

            # 等待泵运行完成
            if wait_for_completion:
                time.sleep(2)  # 等待泵启动
                success = self._wait_for_pump_finish(timeout)
                if success:
                    self.logger.info("齿轮泵运行完成")
                else:
                    self.logger.warning(f"齿轮泵运行超时（超过 {timeout} 秒）")
                return success

            return True

        except Exception as e:
            self.logger.error(f"启动齿轮泵失败: {e}")
            return False

    def _wait_for_pump_finish(self, timeout: float = None) -> bool:
        """
        等待泵运行完成（内部方法）

        :param timeout: 超时时间（秒），默认使用 DEFAULT_TIMEOUT
        :return: 是否在超时前完成
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT

        start_time = time.time()

        while True:
            # 检查是否超时
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.logger.warning(f"等待泵完成超时: {elapsed:.1f}秒")
                return False

            # 读取完成状态
            try:
                done = self.plc.read_coils(self.REG_PUMP_FINISH)[0]
                if done:
                    self.logger.info(f"泵运行完成，用时: {elapsed:.1f}秒")
                    return True
            except Exception as e:
                self.logger.error(f"读取泵状态失败: {e}")
                return False

            time.sleep(self.poll_interval)

    def stop_pump(self) -> bool:
        """
        紧急停止齿轮泵

        :return: 操作是否成功
        """
        try:
            self.logger.info("执行齿轮泵紧急停止")

            # 停止泵控制信号序列
            # 根据原有逻辑：False -> True -> False
            self.plc.write_coil(self.REG_PUMP_CONTROL, False)
            time.sleep(1)
            self.plc.write_coil(self.REG_PUMP_CONTROL, True)
            time.sleep(1)
            self.plc.write_coil(self.REG_PUMP_CONTROL, False)

            self.logger.info("齿轮泵已停止")
            return True

        except Exception as e:
            self.logger.error(f"停止齿轮泵失败: {e}")
            return False


if __name__ == '__main__':
    # 测试代码
    print("=== 齿轮泵控制测试 ===\n")

    # 使用 Mock 模式进行测试
    pump = GearPump(mock=True, poll_interval=0.5)

    # 测试1: 启动泵运行3秒（等待完成）
    print("测试1: 启动泵运行 3 秒...")
    success = pump.start_pump(duration_seconds=3, wait_for_completion=True, timeout=10)
    if success:
        print("✓ 测试1成功：泵运行完成\n")
    else:
        print("✗ 测试1失败：泵运行未完成\n")

    time.sleep(1)

    # 测试2: 启动泵但不等待完成
    print("测试2: 启动泵运行 5 秒（不等待完成）...")
    success = pump.start_pump(duration_seconds=5, wait_for_completion=False)
    if success:
        print("✓ 测试2成功：泵已启动\n")
    else:
        print("✗ 测试2失败：泵启动失败\n")

    # 测试3: 紧急停止泵
    print("测试3: 紧急停止泵...")
    success = pump.stop_pump()
    if success:
        print("✓ 测试3成功：泵已停止\n")
    else:
        print("✗ 测试3失败：泵停止失败\n")

    print("=== 测试完成 ===")
