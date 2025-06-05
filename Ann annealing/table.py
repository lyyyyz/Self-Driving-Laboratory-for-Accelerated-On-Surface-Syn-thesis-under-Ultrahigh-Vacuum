import sys
import time
import subprocess
import os
import signal
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QApplication, QGridLayout, QSizePolicy, QMessageBox, QTabWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
from PyQt5.QtCore import Qt

# 设置字体为 SimHei（黑体），确保系统中已经安装了该字体
plt.rcParams['font.family'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False  # 确保负号正常显示

class ControlPanel(QWidget):
    def __init__(self, start_control_callback, stop_control_callback, adjust_current_callback, pause_callback=None):
        super().__init__()

        # 保存回调函数
        self.start_control_callback = start_control_callback
        self.stop_control_callback = stop_control_callback
        self.adjust_current_callback = adjust_current_callback
        self.pause_callback = pause_callback

        # 设置初始参数
        self.voltage = 25.0  # 默认电压25V
        self.current_default = 3.85  # 默认电流3.85A
        self.heating_rate_default = 1.0  # 默认加热速率

        # 创建数据存储
        self.temperature_data = []
        self.time_data = []
        self.start_time = None

        # 初始化计时器显示
        self.elapsed_time_label = QLabel('Elapsed Time:')
        self.elapsed_time_data = QLabel('0 s')

        # 添加一个标志变量来跟踪是否已经显示过电阻警告
        self.resistance_warning_shown = False

        # 创建界面布局
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Power Control Panel')

        main_layout = QVBoxLayout()

        # =========================
        # 创建标签页（TabWidget）用于区分两种模式
        # =========================
        self.tab_widget = QTabWidget()

        # ----- AI 控制模式页 -----
        ai_tab = QWidget()
        ai_layout = QVBoxLayout()
        # 输入字段布局（电压、电流、温度、时间、加热速率）
        ai_input_grid = QGridLayout()
        ai_input_grid.setSpacing(10)

        max_voltage_label = QLabel('Maximum Voltage (V):')
        self.voltage_input = QLineEdit(str(self.voltage))  # 默认电压

        max_current_label = QLabel('Maximum Current (A):')
        self.current_input = QLineEdit(str(self.current_default))  # 默认电流

        temperature_label = QLabel('Set Temperature (°C):')
        self.temperature_input = QLineEdit()

        time_label = QLabel('Heating Time (s):')
        self.time_input = QLineEdit()

        heating_rate_label = QLabel('Heating Rate (°C/s):')
        self.heating_rate_input = QLineEdit(str(self.heating_rate_default))  # 默认加热速率

        ai_input_grid.addWidget(max_voltage_label, 0, 0)
        ai_input_grid.addWidget(self.voltage_input, 0, 1)
        ai_input_grid.addWidget(max_current_label, 1, 0)
        ai_input_grid.addWidget(self.current_input, 1, 1)
        ai_input_grid.addWidget(temperature_label, 2, 0)
        ai_input_grid.addWidget(self.temperature_input, 2, 1)
        ai_input_grid.addWidget(time_label, 3, 0)
        ai_input_grid.addWidget(self.time_input, 3, 1)
        ai_input_grid.addWidget(heating_rate_label, 4, 0)
        ai_input_grid.addWidget(self.heating_rate_input, 4, 1)

        ai_layout.addLayout(ai_input_grid)

        # 添加 Start 按钮（仅在 AI 模式下使用）
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_control)
        start_layout = QHBoxLayout()
        start_layout.addStretch()
        start_layout.addWidget(self.start_button)
        start_layout.addStretch()
        ai_layout.addLayout(start_layout)

        ai_tab.setLayout(ai_layout)
        self.tab_widget.addTab(ai_tab, "AI 控制模式")

        # ----- 手动控制模式页 -----
        manual_tab = QWidget()
        manual_layout = QVBoxLayout()
        # 在顶部添加 Heating Time 输入框
        time_layout = QHBoxLayout()
        time_label_manual = QLabel('Heating Time (s):')
        self.time_input_manual = QLineEdit()
        self.time_input_manual.setFixedWidth(80)  # 设置固定宽度，让输入框不会过长
        time_layout.addWidget(time_label_manual)
        time_layout.addWidget(self.time_input_manual)
        time_layout.addStretch()  # 在末尾添加伸缩，避免输入框拉伸
        manual_layout.addLayout(time_layout)
        # 电流调整布局
        adjust_current_layout = QHBoxLayout()
        adjust_current_label = QLabel('Adjust Current to Target (A):')
        self.adjust_current_input = QLineEdit()
        self.adjust_current_button = QPushButton('Set')
        self.adjust_current_button.clicked.connect(self.adjust_current)
        adjust_current_layout.addWidget(adjust_current_label)
        adjust_current_layout.addWidget(self.adjust_current_input)
        adjust_current_layout.addWidget(self.adjust_current_button)
        adjust_current_layout.addStretch()  # 右侧拉伸

        manual_layout.addLayout(adjust_current_layout)
        manual_tab.setLayout(manual_layout)
        self.tab_widget.addTab(manual_tab, "手动控制模式")

        # 将标签页添加到主布局中
        main_layout.addWidget(self.tab_widget)

        # 同步两个 Heating Time 输入框：分别将其中一个的修改更新到另一个
        self.time_input.textChanged.connect(self.sync_time_from_ai)
        self.time_input_manual.textChanged.connect(self.sync_time_from_manual)

        manual_tab.setLayout(manual_layout)
        self.tab_widget.addTab(manual_tab, "手动控制模式")

        # =========================
        # 公共控制按钮区域（Stop 和 Pause）
        # =========================
        common_button_layout = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.pause_button = QPushButton('Pause & Exit')
        self.stop_button.clicked.connect(self.stop_control)
        self.pause_button.clicked.connect(self.pause_control)
        common_button_layout.addWidget(self.stop_button)
        common_button_layout.addWidget(self.pause_button)
        main_layout.addLayout(common_button_layout)



        # =========================
        # 信息显示区（使用网格布局）
        # =========================
        info_grid = QGridLayout()
        info_grid.setSpacing(10)

        self.current_label = QLabel('Current:')
        self.current_data = QLabel('Unknown A')

        self.temperature_label = QLabel('Temperature:')
        self.temperature_data_label = QLabel('Unknown °C')

        self.voltage_label = QLabel('Voltage:')
        self.voltage_data = QLabel('Unknown V')

        self.infrared_label = QLabel('Infrared Temp:')
        self.infrared_data = QLabel('Unknown °C')

        self.resistance_label = QLabel('Resistance:')
        self.resistance_data = QLabel('Unknown Ω')

        self.infrared_target_label = QLabel('Infrared Target:')
        self.infrared_target_data = QLabel('Unknown °C')

        # 设置信息字体加粗
        for label in [
            self.current_data, self.temperature_data_label,
            self.voltage_data, self.infrared_data,
            self.resistance_data, self.infrared_target_data
        ]:
            label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # 第一列
        info_grid.addWidget(self.current_label, 0, 0, alignment=Qt.AlignRight)
        info_grid.addWidget(self.current_data, 0, 1, alignment=Qt.AlignLeft)

        info_grid.addWidget(self.voltage_label, 1, 0, alignment=Qt.AlignRight)
        info_grid.addWidget(self.voltage_data, 1, 1, alignment=Qt.AlignLeft)

        info_grid.addWidget(self.resistance_label, 2, 0, alignment=Qt.AlignRight)
        info_grid.addWidget(self.resistance_data, 2, 1, alignment=Qt.AlignLeft)

        # 第二列
        info_grid.addWidget(self.temperature_label, 0, 2, alignment=Qt.AlignRight)
        info_grid.addWidget(self.temperature_data_label, 0, 3, alignment=Qt.AlignLeft)

        info_grid.addWidget(self.infrared_label, 1, 2, alignment=Qt.AlignRight)
        info_grid.addWidget(self.infrared_data, 1, 3, alignment=Qt.AlignLeft)

        info_grid.addWidget(self.infrared_target_label, 2, 2, alignment=Qt.AlignRight)
        info_grid.addWidget(self.infrared_target_data, 2, 3, alignment=Qt.AlignLeft)

        # 添加经过时间显示
        info_grid.addWidget(self.elapsed_time_label, 3, 0, alignment=Qt.AlignRight)
        info_grid.addWidget(self.elapsed_time_data, 3, 1, alignment=Qt.AlignLeft)

        main_layout.addLayout(info_grid)

        # =========================
        # 温度记录图表（实时更新）
        # =========================
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Real-time Temperature Recording')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.set_ylim(0, 500)  # 固定Y轴范围0到500度

        # 初始化时间轴格式化器
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        self.line, = self.ax.plot([], [], 'r-')  # 初始化折线图
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

        # =========================
        # 添加按钮以启动 main_aototest.py
        # =========================
        self.start_auto_test_button = QPushButton('Start Auto Test')
        self.start_auto_test_button.clicked.connect(self.start_auto_test)

        # 添加到界面布局
        main_layout.addWidget(self.start_auto_test_button)

    def start_control(self):
        # 清除旧数据
        self.temperature_data.clear()
        self.time_data.clear()
        self.start_time = time.time()  # 记录当前时间作为起始时间

        # 调用外部的启动控制逻辑，并传递加热速率
        try:
            heating_rate = float(self.heating_rate_input.text())
        except ValueError:
            heating_rate = self.heating_rate_default
        self.start_control_callback(heating_rate)

    def stop_control(self):
        # 调用外部的停止控制逻辑
        self.stop_control_callback()

    def adjust_current(self):
        """当点击手动模式中的 Set 按钮时调用"""
        try:
            target_current = float(self.adjust_current_input.text())
            # 直接调用外部的调电流回调，不进行 control_thread 检测
            self.adjust_current_callback(target_current)
        except ValueError:
            print("Please enter a valid current value")
    
    def start_auto_test(self):
        """关闭当前的 main_ai.py，然后启动 main_autotest.py"""
        try:
            # 获取当前进程 ID
            pid = os.getpid()
            
            # 获取父进程（main_ai.py）的 ID
            parent_pid = os.getppid()
            
            print(f"当前进程 ID: {pid}, 父进程 ID: {parent_pid}")
            
            # 先杀掉 main_ai.py 进程，确保不会重复开启
            os.kill(parent_pid, signal.SIGTERM)
            print(f"已终止 main_ai.py (PID: {parent_pid})")

            # 启动 main_aototest.py
            script_path = os.path.abspath("main_autotest.py")
            subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            QMessageBox.information(self, "Info", "Auto test started successfully!")
            
            # 关闭当前 GUI
            sys.exit(0)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start auto test: {e}")


    def update_temperature_display(self, actual_temperature, infrared_temperature, current_current, current_voltage):
        # 更新数据显示
        self.temperature_data_label.setText(f'{actual_temperature:.3f} °C')
        self.infrared_data.setText(f'{infrared_temperature:.3f} °C')
        self.current_data.setText(f'{current_current:.3f} A')

        if current_voltage is None:
            self.voltage_data.setText('Not measured')
        elif isinstance(current_voltage, str):
            self.voltage_data.setText(current_voltage)
        else:
            self.voltage_data.setText(f'{current_voltage:.3f} V')

        if current_current != 0 and isinstance(current_voltage, (int, float)):
            resistance = current_voltage / current_current
            self.resistance_data.setText(f'{resistance:.2f} Ω')
            if resistance > 30 and not self.resistance_warning_shown:
                self.show_resistance_warning()
                self.resistance_warning_shown = True

        if self.start_time is None:
            self.start_time = time.time()

        current_time = time.time()
        self.time_data.append(datetime.now())
        self.temperature_data.append(actual_temperature)

        if len(self.time_data) > 1 and (current_time - self.start_time) > 600:
            self.time_data.pop(0)
            self.temperature_data.pop(0)

        self.line.set_data(self.time_data, self.temperature_data)
        if len(self.time_data) > 1:
            self.ax.set_xlim([self.time_data[0], self.time_data[-1]])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def show_resistance_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("The resistance wire is abnormal")
        msg.setInformativeText("The resistance detected is greater than 30Ω, please check the resistance wire.")
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def set_infrared_target_temperature_display(self, infrared_target_temperature):
        self.infrared_target_data.setText(f'{infrared_target_temperature:.2f} °C')
    
    def update_elapsed_time(self, elapsed_time):
        self.elapsed_time_data.setText(f'{elapsed_time:.1f} s')

    def show_temperature_failure_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Temperature read failed")
        msg.setInformativeText("Multiple consecutive temperature reading failures have been detected. Please switch to manual control mode.")
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def pause_control(self):
        if self.pause_callback is not None:
            self.pause_callback()
    
    def sync_time_from_ai(self, text):
        """当 AI 模式页的 heating time 发生变化时，同步到手动模式的 heating time 输入框"""
        self.time_input_manual.blockSignals(True)
        if self.time_input_manual.text() != text:
            self.time_input_manual.setText(text)
        self.time_input_manual.blockSignals(False)

    def sync_time_from_manual(self, text):
        """当手动模式页的 heating time 发生变化时，同步到 AI 模式页的 heating time 输入框"""
        self.time_input.blockSignals(True)
        if self.time_input.text() != text:
            self.time_input.setText(text)
        self.time_input.blockSignals(False)



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    def dummy_start():
        print("Start control")

    def dummy_stop():
        print("Stop control")

    def dummy_adjust_current(target_current):
        print(f"Adjusting current to: {target_current} A")

    app = QApplication(sys.argv)
    window = ControlPanel(dummy_start, dummy_stop, dummy_adjust_current)
    window.show()
    sys.exit(app.exec_())
