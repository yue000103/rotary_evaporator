
# 在 Windows 上，可以通过以下步骤创建共享文件夹：
#
# 右键点击你想共享的文件夹 -> 选择 属性 -> 共享 标签 -> 点击 共享。
# 确保网络发现和文件共享是开启的。
# 获取该文件夹的共享路径（例如 \\192.168.1.100\shared_folder）。
import os


class LaserMarking:
    def __init__(self, shared_folder_path):
        """
        初始化 LaserMarking 类，设置共享文件夹路径。
        :param shared_folder_path: 共享文件夹路径
        """
        self.shared_folder_path = shared_folder_path

        # 检查共享文件夹路径是否存在
        if not os.path.exists(self.shared_folder_path):
            raise ValueError(f"指定的共享文件夹路径不存在: {self.shared_folder_path}")

    def write_data_to_file(self, data):
        """
        将数据写入共享文件夹中的 txt 文件。
        :param data: 需要写入文件的数据（数字）
        """
        file_path = os.path.join(self.shared_folder_path, "received_data.txt")

        # 打开文件并写入数据
        try:
            with open(file_path, "a") as file:
                file.write(str(data) + "\n")
            print(f"数据 {data} 已成功写入 {file_path}")
        except Exception as e:
            print(f"写入文件时发生错误: {e}")


# 示例使用：
if __name__ == "__main__":
    shared_folder_path = r"\\192.168.1.100\shared_folder"  # 替换为实际共享文件夹的路径
    laser_marking = LaserMarking(shared_folder_path)

    # 写入数据
    laser_marking.write_data_to_file(12345)
