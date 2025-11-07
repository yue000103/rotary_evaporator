import time

from src.com_control import plc
from src.util.logs_control.setup import device_control_logger


class InjectHeight:
    """注射针高度控制类，用于控制注射针的升降动作"""

    # 寄存器地址定义
    REG_HEIGHT_CONTROL = 307  # 注射针升降控制寄存器 (True=降针, False=升针)

    # 默认延迟时间（秒）
    DEFAULT_DELAY = 1.0

    def __init__(self, mock: bool = False, delay: float = DEFAULT_DELAY):
        """
        初始化注射针高度控制器

        :param mock: 是否启用 Mock 模式，用于测试
        :param delay: 操作后的延迟时间（秒），默认为 1.0 秒
        """
        self.mock = mock
        self.plc = plc
        self.plc.mock = mock
        self.delay = delay
        self.logger = device_control_logger

    def down_height(self) -> bool:
        """
        降低注射针高度

        :return: 操作是否成功
        """
        try:
            self.logger.info("开始降针操作")
            self.plc.write_coil(self.REG_HEIGHT_CONTROL, True)
            time.sleep(self.delay)
            self.logger.info("降针操作完成")
            return True
        except Exception as e:
            self.logger.error(f"降针操作失败: {e}")
            return False

    def up_height(self) -> bool:
        """
        提升注射针高度

        :return: 操作是否成功
        """
        try:
            self.logger.info("开始升针操作")
            self.plc.write_coil(self.REG_HEIGHT_CONTROL, False)
            time.sleep(self.delay)
            self.logger.info("升针操作完成")
            return True
        except Exception as e:
            self.logger.error(f"升针操作失败: {e}")
            return False

if __name__ == '__main__':
    # 测试代码
    height = InjectHeight(mock=True)  # 使用 Mock 模式测试

    # 测试降针
    print("测试降针...")
    if height.down_height():
        print("降针成功")
    else:
        print("降针失败")

    time.sleep(2)

    # 测试升针
    print("\n测试升针...")
    if height.up_height():
        print("升针成功")
    else:
        print("升针失败")
