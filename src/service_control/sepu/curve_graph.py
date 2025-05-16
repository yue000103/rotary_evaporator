import sys
import matplotlib.pyplot as plt
import numpy as np
import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
)


class PlotWithInputs(QWidget):
    def __init__(self, curve_data, vertical_data, sampling_time):
        super().__init__()

        self.curve_data = curve_data
        self.vertical_data = vertical_data
        self.sampling_time = sampling_time
        self.tube_entries = []  # 存储输入的 module_id 和 tube_list

        self.initUI()
        self.plot_fixed_size_curve()  # **先绘制图像**

    def initUI(self):
        layout = QVBoxLayout()

        # 输入框布局
        input_layout = QHBoxLayout()
        self.module_input = QLineEdit()
        self.module_input.setPlaceholderText("输入 module_id_id")

        self.tube_input = QLineEdit()
        self.tube_input.setPlaceholderText("输入 tube_list (逗号分隔)")

        self.module_input.returnPressed.connect(self.add_tube_entry)
        self.tube_input.returnPressed.connect(self.add_tube_entry)

        input_layout.addWidget(QLabel("Method ID:"))
        input_layout.addWidget(self.module_input)
        input_layout.addWidget(QLabel("Tube List:"))
        input_layout.addWidget(self.tube_input)

        layout.addLayout(input_layout)

        # 显示输入内容
        self.display_area = QTextEdit()
        self.display_area.setReadOnly(True)
        layout.addWidget(self.display_area)

        # 开始按钮
        self.start_button = QPushButton("开始")
        self.start_button.clicked.connect(self.start_process)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def add_tube_entry(self):
        """ 记录输入的 module_id 和 tube_list """
        module_id = self.module_input.text().strip()
        tube_list = self.tube_input.text().strip()

        if module_id and tube_list:
            try:
                # **转换 tube_list 为整数列表**
                tube_list_int = [int(x.strip()) for x in tube_list.split(",") if x.strip().isdigit()]
                entry = {"module_id": int(module_id), "tube_list": tube_list_int}
                self.tube_entries.append(entry)
                self.display_area.append(f"Method ID: {module_id}, Tube List: {tube_list_int}")

                # 清空输入框
                self.module_input.clear()
                self.tube_input.clear()
            except ValueError:
                self.display_area.append("错误: Tube List 必须是逗号分隔的整数")

    def start_process(self):
        """ 输出所有输入的数据 """
        print(self.tube_entries)
        self.close()  # **关闭窗口**

    def return_tube(self):
        """ 输出所有输入的数据 """
        return self.tube_entries


    def plot_fixed_size_curve(self):
        """
        绘制固定大小的曲线，并在指定时间范围绘制垂线，同时调整垂线高度，使其稍微上移。
        """
        # 解析时间
        start_time = datetime.datetime.strptime(self.curve_data[0]["time"], "%H:%M:%S")
        times = [(datetime.datetime.strptime(d["time"], "%H:%M:%S") - start_time).total_seconds() for d in self.curve_data]
        values = [d["value"] for d in self.curve_data]

        # 平滑曲线插值
        times_interp = np.linspace(min(times), max(times), num=500)
        values_interp = np.interp(times_interp, times, values)

        # 获取纵坐标范围
        y_min, y_max = min(values), max(values)

        # **创建固定大小的图像**
        fig, ax = plt.subplots(figsize=(12, 6))  # 固定大小

        ax.plot(times_interp, values_interp, label="Smoothed Curve", color="blue")



        # 画垂线，并调整字体大小和位置以增强可见性
        for v in self.vertical_data:
            t_start = (datetime.datetime.strptime(v["time_start"], "%H:%M:%S") - start_time).total_seconds()
            t_end = (datetime.datetime.strptime(v["time_end"], "%H:%M:%S") - start_time).total_seconds()
            mid_time = (t_start + t_end) / 2

            # print(t_start,t_end)

            ax.vlines(x=t_start, ymin=0, ymax=y_max, color="red", linestyle="--", linewidth=1.5)  # **动态调整垂线**
            ax.text(mid_time, y_max, f'{int(v["module_index"]+1)} - {int(v["tube_index"]+1)}',
                    horizontalalignment='center', verticalalignment='bottom',
                    fontsize=12, color='red', fontweight='bold')

        # 设置轴标签和标题
        ax.set_xlabel("Time (seconds)", fontsize=14)
        ax.set_ylabel("Value", fontsize=14)
        ax.set_title("Fixed Size Smoothed Curve", fontsize=16)
        ax.legend(fontsize=12)

        # 禁用网格线
        ax.grid(False)

        # **禁用缩放**
        plt.get_current_fig_manager().full_screen_toggle()
        plt.show()


# 启动应用
if __name__ == "__main__":
    curve_data =  [{'time': '0:00:00', 'value': 50.0}, {'time': '0:00:01', 'value': 50.0}, {'time': '0:00:02', 'value': 50.0}, {'time': '0:00:03', 'value': 50.0}, {'time': '0:00:04', 'value': 50.0}, {'time': '0:00:05', 'value': 50.0}, {'time': '0:00:06', 'value': 50.0}, {'time': '0:00:07', 'value': 50.0}, {'time': '0:00:08', 'value': 50.0}, {'time': '0:00:09', 'value': 50.0}, {'time': '0:00:10', 'value': 50.0}, {'time': '0:00:11', 'value': 50.0}, {'time': '0:00:12', 'value': 50.0}, {'time': '0:00:13', 'value': 50.0}, {'time': '0:00:14', 'value': 50.0}, {'time': '0:00:15', 'value': 50.0}, {'time': '0:00:16', 'value': 50.0}, {'time': '0:00:17', 'value': 50.0}, {'time': '0:00:00', 'value': 50.0}, {'time': '0:00:01', 'value': 50.0}, {'time': '0:00:02', 'value': 50.0}, {'time': '0:00:03', 'value': 50.0}, {'time': '0:00:04', 'value': 50.0}, {'time': '0:00:05', 'value': 50.0}, {'time': '0:00:06', 'value': 50.0}, {'time': '0:00:07', 'value': 50.0}, {'time': '0:00:08', 'value': 50.0}, {'time': '0:00:09', 'value': 50.0}, {'time': '0:00:10', 'value': 50.0}, {'time': '0:00:11', 'value': 50.0}, {'time': '0:00:12', 'value': 50.0}, {'time': '0:00:13', 'value': 50.0}, {'time': '0:00:14', 'value': 50.0}, {'time': '0:00:15', 'value': 50.0}, {'time': '0:00:16', 'value': 50.0}, {'time': '0:00:17', 'value': 50.0}, {'time': '0:00:18', 'value': 50.0}, {'time': '0:00:19', 'value': 50.0}, {'time': '0:00:20', 'value': 50.0}, {'time': '0:00:21', 'value': 50.0}, {'time': '0:00:22', 'value': 50.0}, {'time': '0:00:23', 'value': 50.0}, {'time': '0:00:24', 'value': 50.0}, {'time': '0:00:25', 'value': 50.0}, {'time': '0:00:26', 'value': 50.0}, {'time': '0:00:27', 'value': 50.0}, {'time': '0:00:28', 'value': 50.0}, {'time': '0:00:29', 'value': 50.0}, {'time': '0:00:30', 'value': 50.0}, {'time': '0:00:31', 'value': 50.0}, {'time': '0:00:32', 'value': 50.0}, {'time': '0:00:33', 'value': 50.0}, {'time': '0:00:34', 'value': 50.0}, {'time': '0:00:35', 'value': 50.0}, {'time': '0:00:36', 'value': 50.0}, {'time': '0:00:37', 'value': 50.0}, {'time': '0:00:38', 'value': 50.0}, {'time': '0:00:39', 'value': 50.0}, {'time': '0:00:40', 'value': 50.0}, {'time': '0:00:41', 'value': 50.0}, {'time': '0:00:42', 'value': 50.0}, {'time': '0:00:43', 'value': 50.0}, {'time': '0:00:44', 'value': 50.0}, {'time': '0:00:45', 'value': 50.0}, {'time': '0:00:46', 'value': 50.0}, {'time': '0:00:47', 'value': 50.0}, {'time': '0:00:48', 'value': 50.0}, {'time': '0:00:49', 'value': 50.0}, {'time': '0:00:50', 'value': 50.0}, {'time': '0:00:51', 'value': 50.0}, {'time': '0:00:52', 'value': 50.0}, {'time': '0:00:53', 'value': 50.0}, {'time': '0:00:54', 'value': 50.0}, {'time': '0:00:55', 'value': 50.0}, {'time': '0:00:56', 'value': 50.0}, {'time': '0:00:57', 'value': 50.0}, {'time': '0:00:58', 'value': 50.0}, {'time': '0:00:59', 'value': 50.0}, {'time': '0:01:00', 'value': 50.0}, {'time': '0:01:01', 'value': 50.0}, {'time': '0:01:02', 'value': 50.0}, {'time': '0:01:03', 'value': 50.0}, {'time': '0:01:04', 'value': 50.0}, {'time': '0:01:05', 'value': 50.0}, {'time': '0:01:06', 'value': 50.0}, {'time': '0:01:07', 'value': 50.0}, {'time': '0:01:08', 'value': 50.0}, {'time': '0:01:09', 'value': 50.0}, {'time': '0:01:10', 'value': 50.0}, {'time': '0:01:11', 'value': 50.0}, {'time': '0:01:12', 'value': 50.0}, {'time': '0:01:13', 'value': 50.0}, {'time': '0:01:14', 'value': 50.0}, {'time': '0:01:15', 'value': 50.0}, {'time': '0:01:16', 'value': 50.0}, {'time': '0:01:17', 'value': 50.0}, {'time': '0:01:18', 'value': 50.0}, {'time': '0:01:19', 'value': 50.0}, {'time': '0:01:20', 'value': 50.0}, {'time': '0:01:21', 'value': 50.0}, {'time': '0:01:22', 'value': 50.0}, {'time': '0:01:23', 'value': 50.0}, {'time': '0:01:24', 'value': 50.0}, {'time': '0:01:25', 'value': 50.0}, {'time': '0:01:26', 'value': 50.0}, {'time': '0:01:27', 'value': 50.0}]

    vertical_data = [{'module_index': 0.0, "time_start": "00:00:00", "time_end": "0:00:10", 'tube_index': 0.0}, {'module_index': 0.0, "time_start": "0:00:10", "time_end": "0:00:17", 'tube_index': 1.0}, {'module_index': 0.0, "time_start": "0:00:17", "time_end": "0:00:27", 'tube_index': 2.0}, {'module_index': 0.0, 'time_end': '0:00:37', 'time_start': '0:00:27', 'tube_index': 3.0}, {'module_index': 0.0, "time_start": "0:00:27", "time_end": "0:00:36", 'tube_index': 4.0}, {'module_index': 0.0, "time_start": "0:00:36", "time_end": "0:00:45", 'tube_index': 5.0}, {'module_index': 0.0, "time_start": "0:00:45", "time_end": "0:01:45", 'tube_index': 6.0}]

    sampling_time = 20  # 20分钟

    app = QApplication(sys.argv)
    window = PlotWithInputs(curve_data, vertical_data, sampling_time)
    window.show()
    sys.exit(app.exec_())
