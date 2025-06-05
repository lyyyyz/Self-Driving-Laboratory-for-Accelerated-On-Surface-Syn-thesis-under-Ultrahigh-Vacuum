import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QComboBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from multiprocessing import Pipe
import subprocess  # 用于启动外部程序

class SignalCommunicator(QObject):
    update_valve_status_signal = pyqtSignal(str)

class SubtractionApp(QWidget):
    def __init__(self, pipe, communicator):
        super().__init__()
        self.pipe = pipe
        self.communicator = communicator
        self.initUI()

        # 将信号连接到更新前面板的槽函数
        self.communicator.update_valve_status_signal.connect(self.update_valve_status)

        # 设置定时器，用于检查管道中的更新状态消息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_pipe_for_updates)
        self.timer.start(100)  # 每 100ms 检查一次管道

    def initUI(self):
        self.setWindowTitle('Movement Control App')

        # 总布局
        main_layout = QVBoxLayout()

        # 添加“运动到”按钮
        self.positions = [52, 120, 460, 536, 610, 5362]  # 新增 5362 按钮
        button_layout = QHBoxLayout()
        for pos in self.positions:
            button = QPushButton(f'运动到 {pos}', self)
            button.clicked.connect(lambda checked, p=pos: self.move_to_position(p))
            button_layout.addWidget(button)

        main_layout.addLayout(button_layout)

        # 当前和目标位置显示框
        self.current_position_label = QLabel('当前位置:', self)
        self.current_position = QLineEdit(self)
        self.current_position.setText('0.00')  # 假设初始位置为0.00
        main_layout.addWidget(self.current_position_label)
        main_layout.addWidget(self.current_position)

        self.target_position_label = QLabel('目标位置:', self)
        self.target_position = QLineEdit(self)
        main_layout.addWidget(self.target_position_label)
        main_layout.addWidget(self.target_position)

        # 阀门状态显示和手动控制
        self.valve_status_label = QLabel('阀门状态:', self)
        self.valve_status_dropdown = QComboBox(self)
        self.valve_status_dropdown.addItem("关闭")
        self.valve_status_dropdown.addItem("打开")
        self.valve_status_dropdown.currentIndexChanged.connect(self.manual_valve_status_change)
        main_layout.addWidget(self.valve_status_label)
        main_layout.addWidget(self.valve_status_dropdown)

        # 阀门手动控制按钮
        self.valve_open_button = QPushButton('开阀门', self)
        self.valve_open_button.clicked.connect(self.open_valve)
        main_layout.addWidget(self.valve_open_button)

        self.valve_close_button = QPushButton('关阀门', self)
        self.valve_close_button.clicked.connect(self.close_valve)
        main_layout.addWidget(self.valve_close_button)

        # 添加X轴调整位置
        self.xaxis_current_position_label = QLabel('X轴原本位置:', self)
        self.xaxis_current_position = QLineEdit(self)
        self.xaxis_current_position.setText('0.00')  # 假设X轴初始位置为0.00
        main_layout.addWidget(self.xaxis_current_position_label)
        main_layout.addWidget(self.xaxis_current_position)

        self.xaxis_target_position_label = QLabel('X轴目标位置:', self)
        self.xaxis_target_position = QLineEdit(self)
        main_layout.addWidget(self.xaxis_target_position_label)
        main_layout.addWidget(self.xaxis_target_position)

        # 添加启动X轴调整按钮
        self.start_xaxis_button = QPushButton('启动X轴调整', self)
        self.start_xaxis_button.clicked.connect(self.start_xaxis_adjustment)
        main_layout.addWidget(self.start_xaxis_button)

        # 添加Y轴调整位置
        self.yaxis_current_position_label = QLabel('Y轴原本位置:', self)
        self.yaxis_current_position = QLineEdit(self)
        self.yaxis_current_position.setText('0.00')  # 假设Y轴初始位置为0.00
        main_layout.addWidget(self.yaxis_current_position_label)
        main_layout.addWidget(self.yaxis_current_position)

        self.yaxis_target_position_label = QLabel('Y轴目标位置:', self)
        self.yaxis_target_position = QLineEdit(self)
        main_layout.addWidget(self.yaxis_target_position_label)
        main_layout.addWidget(self.yaxis_target_position)

        # 添加启动Y轴调整按钮
        self.start_yaxis_button = QPushButton('启动Y轴调整', self)
        self.start_yaxis_button.clicked.connect(self.start_yaxis_adjustment)
        main_layout.addWidget(self.start_yaxis_button)

        # 添加急停按钮
        self.stop_button = QPushButton('急停', self)
        self.stop_button.setStyleSheet("background-color: red; color: white;")  # 急停按钮设为红色
        self.stop_button.clicked.connect(self.stop_movement)
        main_layout.addWidget(self.stop_button)

        # 添加“启动加热”按钮
        self.heat_button = QPushButton('启动加热', self)
        self.heat_button.clicked.connect(self.start_heating)
        main_layout.addWidget(self.heat_button)

        # 添加“启动”按钮，执行移动
        self.start_button = QPushButton('启动', self)
        self.start_button.clicked.connect(self.start_movement)
        main_layout.addWidget(self.start_button)

        self.setLayout(main_layout)

    def check_pipe_for_updates(self):
        """检查管道中的状态更新消息"""
        if self.pipe.poll():  # 检查管道是否有消息
            data = self.pipe.recv()  # 接收消息
            print(f"从管道中收到消息: {data}")  # 添加调试信息
            if isinstance(data, tuple) and data[0] == "UPDATE_VALVE_STATUS":
                valve_status = data[1]
                print(f"收到阀门状态更新: {valve_status}")  # 添加调试信息
                self.communicator.update_valve_status_signal.emit(valve_status)  # 发射信号到槽函数
            elif isinstance(data, tuple) and data[0] == "UPDATE_X_POSITION":
                updated_x = data[1]
                self.xaxis_current_position.setText(str(updated_x))  # 更新X轴原本位置
                print(f"X轴原本位置更新为: {updated_x}")
            elif isinstance(data, tuple) and data[0] == "UPDATE_Y_POSITION":
                updated_y = data[1]
                self.yaxis_current_position.setText(str(updated_y))  # 更新Y轴原本位置
                print(f"Y轴原本位置更新为: {updated_y}")
            elif data == "REQUEST_XY_POSITION":
                # 返回X轴和Y轴的原本位置
                x_position = float(self.xaxis_current_position.text())
                y_position = float(self.yaxis_current_position.text())
                print(f"发送当前X轴原本位置: {x_position}, Y轴原本位置: {y_position}")
                # 将X、Y原本和目标位置发送回 move.py
                target_x = float(self.xaxis_target_position.text())
                target_y = float(self.yaxis_target_position.text())
                self.pipe.send(('UPDATE_XY_POSITION', x_position, y_position, target_x, target_y))  # 发送四个坐标信息

    def move_to_position(self, target_position):
        """更新目标位置并在输入框中显示，同时发送 X 和 Y 目标位置"""
        # 根据目标位置设置 X 和 Y 轴的目标值
        if target_position == 52:
            x_target = -8
            y_target = 10
        elif target_position == 120:
            x_target = -2
            y_target = 6
        elif target_position in [460, 536, 610, 5362]:
            x_target = -2
            y_target = 6
        else:
            x_target = float(self.xaxis_target_position.text())
            y_target = float(self.yaxis_target_position.text())

        # 更新前面板的显示
        self.target_position.setText(str(target_position))
        self.xaxis_target_position.setText(str(x_target))
        self.yaxis_target_position.setText(str(y_target))

        # 发送目标位置、X 和 Y 目标位置给 move.py
        self.pipe.send((target_position, x_target, y_target))
        print(f"发送目标位置: {target_position}, 目标 X: {x_target}, 目标 Y: {y_target}")

    def start_movement(self):
        """根据目标位置进行移动操作并更新当前位置"""
        try:
            # 获取当前和目标位置
            value1 = float(self.current_position.text())
            value2 = float(self.target_position.text())

            # 计算绝对值和方向
            result = value2 - value1
            abs_value = abs(result)
            sign_value = '1' if result >= 0 else '0'

            # 将四个值放入管道中，分别是abs_value, sign_value, value1, value2
            self.pipe.send((abs_value, sign_value, value1, value2))

            # 更新当前位置
            self.current_position.setText(str(value2))

        except ValueError:
            print("输入的值无效，请输入有效数字")

    def start_xaxis_adjustment(self):
        """根据输入的X轴原本位置和目标位置进行X轴调整"""
        try:
            # 获取X轴原本位置和目标位置
            x_current_position = float(self.xaxis_current_position.text())
            x_target_position = float(self.xaxis_target_position.text())

            # 进入X轴调整位置
            self.pipe.send("XPOSITION_MOVE_IN")

            # 根据需要前进或后退
            while x_current_position != x_target_position:
                if x_current_position < x_target_position:
                    self.pipe.send("XPOSITION_TARGET_01MM")  # 前进1mm
                    x_current_position += 1  # 更新当前位置
                elif x_current_position > x_target_position:
                    self.pipe.send("XPOSITION_TARGET_10MM")  # 退后1mm
                    x_current_position -= 1  # 更新当前位置

            # 完成调整后，退出X轴调整位置
            self.pipe.send("XPOSITION_MOVE_OUT")

            # 更新原本位置为目标位置
            self.xaxis_current_position.setText(str(x_target_position))

        except ValueError:
            print("输入的X轴值无效，请输入有效数字")

    def start_yaxis_adjustment(self):
        """根据输入的Y轴原本位置和目标位置进行Y轴调整"""
        try:
            # 获取Y轴原本位置和目标位置
            y_current_position = float(self.yaxis_current_position.text())
            y_target_position = float(self.yaxis_target_position.text())

            # 进入Y轴调整位置
            self.pipe.send("YPOSITION_MOVE_IN")

            # 根据需要前进或后退
            while y_current_position != y_target_position:
                if y_current_position < y_target_position:
                    self.pipe.send("YPOSITION_TARGET_01MM")  # 前进1mm
                    y_current_position += 1  # 更新当前位置
                elif y_current_position > y_target_position:
                    self.pipe.send("YPOSITION_TARGET_10MM")  # 退后1mm
                    y_current_position -= 1  # 更新当前位置

            # 完成调整后，退出Y轴调整位置
            self.pipe.send("YPOSITION_MOVE_OUT")

            # 更新原本位置为目标位置
            self.yaxis_current_position.setText(str(y_target_position))

        except ValueError:
            print("输入的Y轴值无效，请输入有效数字")

    def open_valve(self):
        """手动开阀门，发送信号给move.py"""
        self.pipe.send("OPEN_VALVE")  # 发送开阀门的信号

    def close_valve(self):
        """手动关阀门，发送信号给move.py"""
        self.pipe.send("CLOSE_VALVE")  # 发送关阀门的信号

    def stop_movement(self):
        """向管道发送急停信号"""
        self.pipe.send("STOP")  # 发送急停信号

    def manual_valve_status_change(self):
        """当用户手动选择阀门状态时，更新前面板的显示并发送信号给move.py更新valve_status"""
        selected_status = self.valve_status_dropdown.currentText()
        print(f"手动选择的阀门状态: {selected_status}")
        
        # 仅更新状态，不触发机械臂动作
        if selected_status == "打开":
            self.pipe.send("UPDATE_VALVE_STATUS_OPEN")
        elif selected_status == "关闭":
            self.pipe.send("UPDATE_VALVE_STATUS_CLOSED")

    def update_valve_status(self, status):
        """更新阀门状态，基于机械臂的实际操作"""
        print(f"更新阀门状态为: {status}")  # 添加调试信息
        if status == 'open':
            self.valve_status_dropdown.setCurrentIndex(1)  # 设置为"打开"
        else:
            self.valve_status_dropdown.setCurrentIndex(0)  # 设置为"关闭"

    def start_heating(self):
        """启动加热，运行外部程序"""
        try:
            # 使用 subprocess 运行 E:\AIlab\anneal\main.py
            subprocess.run(["python", "E:\\AIlab\\anneal\\main.py"], check=True)
            print("加热程序启动成功")
        except subprocess.CalledProcessError as e:
            print(f"加热程序启动失败: {e}")

    # 捕捉窗口关闭事件
    def closeEvent(self, event):
        self.pipe.send(None)  # 向管道发送终止信号，确保主进程也退出
        event.accept()

def run_app(pipe):
    app = QApplication(sys.argv)

    # 信号发射器
    communicator = SignalCommunicator()

    ex = SubtractionApp(pipe, communicator)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()  # 使用Pipe进行进程通信
    run_app(parent_conn)
