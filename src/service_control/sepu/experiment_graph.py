import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QBrush
import json


class DraggablePoint(QGraphicsEllipseItem):
    """ 可拖拽的点 """
    def __init__(self, x, y, parent=None):
        super().__init__(-5, -5, 10, 10, parent)
        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setPos(x, y)
        self.elution_curve = []
        self.flowRate = 40
        self.sampling_time = 0
        self.total_flow_rate = 0

    def get_coordinates(self):
        """ 获取点的时间和流速信息 """
        x_time = int(self.x() / 50)  # X 轴按分钟计算
        pumpB = max(0, min(100, int((200 - self.y()) / 2)))  # 限制 pumpB 范围 0-100
        pumpA = 100 - pumpB
        return {"time": x_time, "pumpB": pumpB, "pumpA": pumpA, "flowRate": self.flowRate}


class ExperimentDialog(QDialog):
    """ 实验设置弹窗 """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("实验设置")
        self.resize(800, 600)

        # 布局
        layout = QVBoxLayout()

        # 输入框
        self.total_time_label = QLabel("实验总时间 (分钟):")
        self.total_time_input = QLineEdit()
        self.total_time_input.setPlaceholderText("请输入实验总时间")

        self.total_flow_label = QLabel("总流速:")
        self.total_flow_input = QLineEdit()
        self.total_flow_input.setPlaceholderText("请输入实验总流速")

        self.time_label = QLabel("实验时间 (分钟):")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("请输入实验时间")

        self.flow_label = QLabel("流速:")
        self.flow_input = QLineEdit()
        self.flow_input.setPlaceholderText("请输入流速")

        # 图形视图
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # 添加坐标系
        self.x_max = 10  # 初始横坐标最大时间
        self.y_max = 100  # 纵坐标范围 0-100
        self.points = []  # 存储所有的点
        self.lines = []  # 存储所有连线
        self.draw_axes()

        # 按钮
        self.add_point_btn = QPushButton("添加点")
        self.add_point_btn.clicked.connect(self.add_point)

        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.clicked.connect(self.confirm_points)

        self.total_time_input.textChanged.connect(self.update_x_max)

        # 添加到布局
        layout.addWidget(self.total_time_label)
        layout.addWidget(self.total_time_input)

        layout.addWidget(self.total_flow_label)
        layout.addWidget(self.total_flow_input)

        layout.addWidget(self.time_label)
        layout.addWidget(self.time_input)

        layout.addWidget(self.flow_label)
        layout.addWidget(self.flow_input)
        layout.addWidget(self.view)
        layout.addWidget(self.add_point_btn)
        layout.addWidget(self.confirm_btn)

        self.setLayout(layout)

    def draw_axes(self):
        """ 画坐标系 """
        self.scene.clear()

        # 画 X 轴
        self.scene.addLine(0, 200, self.x_max * 50, 200, QPen(Qt.black))

        # 画 Y 轴
        self.scene.addLine(0, 0, 0, 200, QPen(Qt.black))

        # X 轴刻度
        for i in range(self.x_max + 1):
            self.scene.addLine(i * 50, 195, i * 50, 205, QPen(Qt.black))
            self.scene.addText(str(i)).setPos(i * 50 - 5, 210)

        # Y 轴刻度
        for i in range(0, self.y_max + 1, 20):
            self.scene.addLine(-5, 200 - i * 2, 5, 200 - i * 2, QPen(Qt.black))
            self.scene.addText(str(i)).setPos(-30, 200 - i * 2 - 5)

        # 重新绘制所有点和连线
        self.redraw_points_and_lines()

    def add_point(self):
        """ 添加可拖拽的点 """
        x_value = int(self.time_input.text()) if self.time_input.text().isdigit() else 0
        y_value = int(self.flow_input.text()) if self.flow_input.text().isdigit() else 0


        # 只在必要时更新坐标轴，防止递归调用
        # if x_value > self.x_max:
        #     self.x_max = x_value
        #     self.scene.clear()  # 避免重复叠加元素
        #     self.draw_axes()

        point = DraggablePoint(x_value * 50, 200 - y_value * 2)
        self.scene.addItem(point)
        self.points.append(point)



        self.redraw_points_and_lines()

    def update_x_max(self):
        """ 更新 X 轴最大值，避免无限重绘 """
        try:
            new_x_max = int(self.total_time_input.text())


            if new_x_max > self.x_max:
                self.x_max = new_x_max
                # self.scene.clear()  # 避免无限重绘
                self.draw_axes()
        except ValueError:
            pass

    def redraw_points_and_lines(self):
        """ 重新绘制所有点和连线，防止 Qt 事件循环阻塞 """
        try:
            # 清除已有的连线
            for line in self.lines:
                self.scene.removeItem(line)
            self.lines.clear()
            # print("self.points",self.points)
            elution_curve = [point.get_coordinates() for point in sorted(self.points, key=lambda p: p.x())]
            # print("elution_curve",elution_curve)

            # 按时间排序点
            self.points.sort(key=lambda p: p.x())

            # 画连线
            if len(self.points) > 1:
                pen = QPen(Qt.red)
                pen.setWidth(2)
                for i in range(len(self.points) - 1):
                    line = self.scene.addLine(
                        self.points[i].x(), self.points[i].y(),
                        self.points[i + 1].x(), self.points[i + 1].y(), pen
                    )
                    self.lines.append(line)

        except Exception as e:
            print(f"Redraw failed: {e}")

    def confirm_points(self):
        """ 确认实验点，输出格式化数据，并关闭窗口 """
        self.redraw_points_and_lines()  # 确保点连接正确
        self.elution_curve = [point.get_coordinates() for point in sorted(self.points, key=lambda p: p.x())]
        self.sampling_time = int(self.total_time_input.text())
        self.total_flow_rate = int(self.total_flow_input.text())
        self.accept()  # 关闭窗口


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = ExperimentDialog()
    dialog.exec_()
