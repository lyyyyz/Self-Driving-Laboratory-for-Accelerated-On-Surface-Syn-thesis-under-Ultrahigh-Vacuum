import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QComboBox, QGridLayout
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from multiprocessing import Pipe

class SignalCommunicator(QObject):
    update_valve_status_signal = pyqtSignal(str)

class SubtractionApp(QWidget):
    def __init__(self, pipe, communicator):
        super().__init__()
        self.pipe = pipe
        self.communicator = communicator
        self.target_position_value = None
        self.x_target = None
        self.y_target = None
        self.fai_target = None
        self.initUI()

        # 信号连接
        self.communicator.update_valve_status_signal.connect(self.update_valve_status)

        # 定时器检查
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_pipe_for_updates)
        self.timer.start(100)

    def initUI(self):
        self.setWindowTitle('Movement Control App')
        main_layout = QVBoxLayout()

        # 创建布局
        positions = [("STM", 52), ("Wait to STM", 120), ("Wait for valve", 460), ("Sputter/Anneal", 536), ("Evaporation", 5362), ("Wait for evaporation", 610)]
        button_layout = QHBoxLayout()
        for label, pos in positions:
            button = QPushButton(f'{label}', self)
            button.clicked.connect(lambda checked, p=pos: self.move_to_position(p))
            button_layout.addWidget(button)
        
        main_layout.addLayout(button_layout)

        # 创建阀门状态
        valve_layout = QHBoxLayout()
        self.valve_status_label = QLabel('Valve Status:', self)
        self.valve_status_dropdown = QComboBox(self)
        self.valve_status_dropdown.addItem("Closed")
        self.valve_status_dropdown.addItem("Opened")
        self.valve_status_dropdown.currentIndexChanged.connect(self.manual_valve_status_change)

        self.valve_open_button = QPushButton('Open Valve', self)
        self.valve_open_button.clicked.connect(self.open_valve)
        self.valve_close_button = QPushButton('Close Valve', self)
        self.valve_close_button.clicked.connect(self.close_valve)

        valve_layout.addWidget(self.valve_status_label)
        valve_layout.addWidget(self.valve_status_dropdown)
        valve_layout.addWidget(self.valve_open_button)
        valve_layout.addWidget(self.valve_close_button)

        main_layout.addLayout(valve_layout)

        # Z轴
        z_axis_layout = QHBoxLayout()
        self.current_position_label = QLabel('Z Axis Current Position:', self)
        self.current_position = QLineEdit(self)
        self.current_position.setText('0.00')
        self.target_position_label = QLabel('Z Axis Target Position:', self)
        self.target_position = QLineEdit(self)

        z_axis_layout.addWidget(self.current_position_label)
        z_axis_layout.addWidget(self.current_position)
        z_axis_layout.addWidget(self.target_position_label)
        z_axis_layout.addWidget(self.target_position)

        main_layout.addLayout(z_axis_layout)

        # X轴
        x_axis_layout = QHBoxLayout()
        self.xaxis_current_position_label = QLabel('X Axis Current Position:', self)
        self.xaxis_current_position = QLineEdit(self)
        self.xaxis_current_position.setText('0.00')
        self.xaxis_target_position_label = QLabel('X Axis Target Position:', self)
        self.xaxis_target_position = QLineEdit(self)
        self.start_xaxis_button = QPushButton('Adjust X Axis', self)
        self.start_xaxis_button.clicked.connect(self.start_xaxis_adjustment)

        x_axis_layout.addWidget(self.xaxis_current_position_label)
        x_axis_layout.addWidget(self.xaxis_current_position)
        x_axis_layout.addWidget(self.xaxis_target_position_label)
        x_axis_layout.addWidget(self.xaxis_target_position)
        x_axis_layout.addWidget(self.start_xaxis_button)

        main_layout.addLayout(x_axis_layout)

        # Y轴
        y_axis_layout = QHBoxLayout()
        self.yaxis_current_position_label = QLabel('Y Axis Current Position:', self)
        self.yaxis_current_position = QLineEdit(self)
        self.yaxis_current_position.setText('0.00')
        self.yaxis_target_position_label = QLabel('Y Axis Target Position:', self)
        self.yaxis_target_position = QLineEdit(self)
        self.start_yaxis_button = QPushButton('Adjust Y Axis', self)
        self.start_yaxis_button.clicked.connect(self.start_yaxis_adjustment)

        y_axis_layout.addWidget(self.yaxis_current_position_label)
        y_axis_layout.addWidget(self.yaxis_current_position)
        y_axis_layout.addWidget(self.yaxis_target_position_label)
        y_axis_layout.addWidget(self.yaxis_target_position)
        y_axis_layout.addWidget(self.start_yaxis_button)

        main_layout.addLayout(y_axis_layout)

        # FAI轴
        fai_axis_layout = QHBoxLayout()
        self.fai_current_position_label = QLabel('FAI Current Position:', self)
        self.fai_current_position = QLineEdit(self)
        self.fai_current_position.setText('5')
        self.fai_target_position_label = QLabel('FAI Target Position:', self)
        self.fai_target_position = QLineEdit(self)
        self.start_fai_button = QPushButton('Adjust FAI Axis', self)
        self.start_fai_button.clicked.connect(self.start_fai_adjustment)

        fai_axis_layout.addWidget(self.fai_current_position_label)
        fai_axis_layout.addWidget(self.fai_current_position)
        fai_axis_layout.addWidget(self.fai_target_position_label)
        fai_axis_layout.addWidget(self.fai_target_position)
        fai_axis_layout.addWidget(self.start_fai_button)

        main_layout.addLayout(fai_axis_layout)

        # 急停和启动按钮
        button_layout = QHBoxLayout()
        self.stop_button = QPushButton('STOP', self)
        self.stop_button.setStyleSheet("background-color: red; color: white;")
        self.stop_button.clicked.connect(self.stop_movement)

        self.start_button = QPushButton('START', self)
        self.start_button.clicked.connect(self.start_movement)

        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.start_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def check_pipe_for_updates(self):
        if self.pipe.poll():
            data = self.pipe.recv()
            if isinstance(data, tuple) and data[0] == "UPDATE_VALVE_STATUS":
                valve_status = data[1]
                self.communicator.update_valve_status_signal.emit(valve_status)
            elif isinstance(data, tuple) and data[0] == "UPDATE_X_POSITION":
                updated_x = data[1]
                self.xaxis_current_position.setText(str(updated_x))
            elif isinstance(data, tuple) and data[0] == "UPDATE_Y_POSITION":
                updated_y = data[1]
                self.yaxis_current_position.setText(str(updated_y))

    def move_to_position(self, target_position):
        """点击按钮时仅保存目标位置，并更新前面板显示"""
        if target_position == 52:
            self.x_target = -8
            self.y_target = 10
            self.fai_target = 5
        elif target_position == 120:
            self.x_target = -2
            self.y_target = 6
            self.fai_target = 5
        elif target_position == 460:
            self.x_target = -2
            self.y_target = 6
            self.fai_target = 5
        elif target_position == 536:
            self.x_target = -2
            self.y_target = 6
            self.fai_target = 5
        elif target_position == 5362:
            self.x_target = -2
            self.y_target = 6
            target_position = 536
            self.fai_target = 135
        elif target_position == 610:
            self.x_target = -2
            self.y_target = 6
            self.fai_target = 5

        # 保存目标位置
        self.target_position_value = target_position

        # 更新前面板显示
        self.target_position.setText(str(target_position))
        self.xaxis_target_position.setText(str(self.x_target))
        self.yaxis_target_position.setText(str(self.y_target))
        self.fai_target_position.setText(str(self.fai_target))

    def start_movement(self):
        """点击启动按钮后再发送运动指令"""
        if self.target_position_value is not None:
            self.pipe.send((self.target_position_value, self.x_target, self.y_target, self.fai_target))
            print(f"发送运动指令: 目标位置 {self.target_position_value}, X {self.x_target}, Y {self.y_target}, FAI {self.fai_target}")

    def start_xaxis_adjustment(self):
        """X轴调整逻辑"""
        try:
            x_current_position = float(self.xaxis_current_position.text())
            x_target_position = float(self.xaxis_target_position.text())
            self.pipe.send("XPOSITION_MOVE_IN")
            while x_current_position != x_target_position:
                if x_current_position < x_target_position:
                    self.pipe.send("XPOSITION_TARGET_01MM")
                    x_current_position += 1
                elif x_current_position > x_target_position:
                    self.pipe.send("XPOSITION_TARGET_10MM")
                    x_current_position -= 1
            self.pipe.send("XPOSITION_MOVE_OUT")
            self.xaxis_current_position.setText(str(x_target_position))
        except ValueError:
            print("Invalid X axis value")

    def start_yaxis_adjustment(self):
        """Y轴调整逻辑"""
        try:
            y_current_position = float(self.yaxis_current_position.text())
            y_target_position = float(self.yaxis_target_position.text())
            self.pipe.send("YPOSITION_MOVE_IN")
            while y_current_position != y_target_position:
                if y_current_position < y_target_position:
                    self.pipe.send("YPOSITION_TARGET_01MM")
                    y_current_position += 1
                elif y_current_position > y_target_position:
                    self.pipe.send("YPOSITION_TARGET_10MM")
                    y_current_position -= 1
            self.pipe.send("YPOSITION_MOVE_OUT")
            self.yaxis_current_position.setText(str(y_target_position))
        except ValueError:
            print("Invalid Y axis value")

    def start_fai_adjustment(self):
        """FAI 轴调整逻辑"""
        try:
            fai_current_position = int(self.fai_current_position.text())
            fai_target_position = int(self.fai_target_position.text())

            if fai_target_position not in [5, 135]:
                print("FAI axis can only be set to 5 or 135")
                return

            self.pipe.send("FAI_GET_IN")
            if fai_current_position == 5 and fai_target_position == 135:
                self.pipe.send("FAI_5MOVE135")
            elif fai_current_position == 135 and fai_target_position == 5:
                self.pipe.send("FAI_135MOVE5")

            self.pipe.send("FAI_GET_OUT")
            self.fai_current_position.setText(str(fai_target_position))
        except ValueError:
            print("Invalid FAI axis value")

    def open_valve(self):
        self.pipe.send("OPEN_VALVE")

    def close_valve(self):
        self.pipe.send("CLOSE_VALVE")

    def stop_movement(self):
        self.pipe.send("STOP")

    def manual_valve_status_change(self):
        selected_status = self.valve_status_dropdown.currentText()
        if selected_status == "Opened":
            self.pipe.send("UPDATE_VALVE_STATUS_OPEN")
        elif selected_status == "Closed":
            self.pipe.send("UPDATE_VALVE_STATUS_CLOSED")

    def update_valve_status(self, status):
        if status == 'open':
            self.valve_status_dropdown.setCurrentIndex(1)
        else:
            self.valve_status_dropdown.setCurrentIndex(0)

    def closeEvent(self, event):
        self.pipe.send(None)
        event.accept()

def run_app(pipe):
    app = QApplication(sys.argv)
    communicator = SignalCommunicator()
    ex = SubtractionApp(pipe, communicator)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    run_app(parent_conn)