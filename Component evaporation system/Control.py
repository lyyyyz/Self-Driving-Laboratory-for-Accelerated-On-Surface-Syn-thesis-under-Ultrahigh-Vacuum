import sys
import time
import csv
from PyQt5.QtCore import pyqtSlot, QThread
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QDialog, QMessageBox, QTextEdit
)
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from QCM import QCMDataCollector
from Power import PowerController
from logic import EvaporationLogic

# 设置全局字体支持中文
rcParams['font.sans-serif'] = ['SimHei']
rcParams['axes.unicode_minus'] = False

HISTORY_FILE = "evaporation_history.csv"

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("登录验证")
        self.setGeometry(400, 200, 300, 150)

        layout = QVBoxLayout()
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("用户名")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit(self)
        self.pass_input.setPlaceholderText("密码")
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass_input)

        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.check_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def check_login(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        if username == "admin" and password == "115513":
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "用户名或密码错误")

class MoleculeInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("分子信息输入")
        self.setGeometry(400, 300, 300, 220)

        self.layout = QVBoxLayout()

        self.molecule_input = QLineEdit(self)
        self.molecule_input.setPlaceholderText("请输入分子名称")
        self.layout.addWidget(self.molecule_input)

        self.time_input = QLineEdit(self)
        self.time_input.setPlaceholderText("日期")
        self.layout.addWidget(self.time_input)

        self.confirm_button = QPushButton("开始设置参数")
        self.confirm_button.clicked.connect(self.accept)
        self.layout.addWidget(self.confirm_button)

        self.setLayout(self.layout)

    def get_inputs(self):
        return self.molecule_input.text(), self.time_input.text()

class HistoryDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录")
        self.setGeometry(400, 200, 400, 300)

        layout = QVBoxLayout()
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)

        self.setLayout(layout)
        self.load_history()

    def load_history(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                lines = [f"分子: {row[0]}    日期: {row[1]}    电流: {row[2]} A" for row in reader]
                self.history_text.setText("\n".join(lines))
        except FileNotFoundError:
            self.history_text.setText("暂无记录")

class PowerThread(QThread):
    def __init__(self, power_controller, max_voltage, target_current):
        super().__init__()
        self.power_controller = power_controller
        self.max_voltage = max_voltage
        self.target_current = target_current

    def run(self):
        try:
            self.power_controller.connect()
            self.power_controller.initialize()
            self.power_controller.set_voltage_current(self.max_voltage, 0.0)
            self.power_controller.gradual_current_increase(max_current=self.target_current)
        except Exception as e:
            print(f"电源控制出错: {e}")

class ControlPanel(QWidget):
    def __init__(self, molecule_name="", experiment_time=""):
        super().__init__()
        self.setWindowTitle("QCM 控制面板")
        self.setGeometry(100, 100, 800, 600)

        self.molecule_name = molecule_name
        self.experiment_time = experiment_time

        self.layout = QVBoxLayout()



        self.max_voltage_input = QLineEdit(self)
        self.max_voltage_input.setPlaceholderText("最大电压")
        self.layout.addWidget(self.max_voltage_input)

        self.max_current_input = QLineEdit(self)
        self.max_current_input.setPlaceholderText("最大电流")
        self.layout.addWidget(self.max_current_input)

        self.target_current_input = QLineEdit(self)
        self.target_current_input.setPlaceholderText("目标电流")
        self.layout.addWidget(self.target_current_input)

        self.start_button = QPushButton("启动蒸发", self)
        self.start_button.clicked.connect(self.start_evaporation)
        self.layout.addWidget(self.start_button)

        self.history_button = QPushButton("查看历史记录", self)
        self.history_button.clicked.connect(self.show_history)
        self.layout.addWidget(self.history_button)

        self.molecule_label = QLabel(f"分子名称: {self.molecule_name}，日期: {self.experiment_time}", self)
        self.layout.addWidget(self.molecule_label)

        self.freq_label = QLabel("频率: 0 Hz", self)
        self.layout.addWidget(self.freq_label)
        self.thickness_label = QLabel("膜厚: 0 Å", self)
        self.layout.addWidget(self.thickness_label)
        self.rate_label = QLabel("速率: 0 Å/min", self)
        self.layout.addWidget(self.rate_label)

        self.figure, (self.ax_thickness, self.ax_rate) = plt.subplots(2, 1, figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.thickness_data = []
        self.rate_data = []

        self.setLayout(self.layout)

        self.power_controller = PowerController('USB0::0x2EC7::0x320C::804634011797110022::2::INSTR')
        self.logic = None
        self.qcm_collector = None
        self.power_thread = None

    def start_evaporation(self):
        try:
            max_voltage = float(self.max_voltage_input.text())
            max_current = float(self.max_current_input.text())
            target_current = float(self.target_current_input.text())
        except ValueError:
            print("请输入有效的电源参数")
            return

        self.power_controller.set_max_current_limit(max_current)
        self.logic = EvaporationLogic(self.power_controller)

        self.power_thread = PowerThread(
            power_controller=self.power_controller,
            max_voltage=max_voltage,
            target_current=target_current
        )
        self.power_thread.start()

        self.qcm_collector = QCMDataCollector()
        self.qcm_collector.thickness_signal.connect(self.update_thickness)
        self.qcm_collector.rate_signal.connect(self.update_rate)
        self.qcm_collector.frequency_signal.connect(self.update_frequency)
        self.qcm_collector.start()

    def show_history(self):
        dlg = HistoryDialog()
        dlg.exec_()

    @pyqtSlot(float)
    def update_thickness(self, thickness):
        self.thickness_data.append(thickness)
        if len(self.thickness_data) > 120:
            self.thickness_data.pop(0)

        self.ax_thickness.clear()
        self.ax_thickness.plot(self.thickness_data, label='膜厚 (Å)')
        self.ax_thickness.set_title("膜厚变化")
        self.ax_thickness.set_xlabel("时间 (秒)")
        self.ax_thickness.set_ylabel("膜厚 (Å)")
        self.ax_thickness.legend()

        self.canvas.draw()
        self.thickness_label.setText(f"膜厚: {thickness:.2f} Å")

    @pyqtSlot(float)
    def update_rate(self, rate):
        self.rate_data.append(rate)
        if len(self.rate_data) > 120:
            self.rate_data.pop(0)

        self.ax_rate.clear()
        self.ax_rate.plot(self.rate_data, label='速率 (Å/分钟)', color='r')
        self.ax_rate.set_title("速率变化")
        self.ax_rate.set_xlabel("时间 (分钟)")
        self.ax_rate.set_ylabel("速率 (Å/分钟)")
        self.ax_rate.legend()

        self.canvas.draw()
        self.rate_label.setText(f"速率: {rate:.2f} Å/min")

        if self.logic:
            self.logic.add_rate(rate)

    @pyqtSlot(str)
    def update_frequency(self, frequency):
        self.freq_label.setText(f"频率: {frequency} Hz")

    def closeEvent(self, event):
        print("窗口关闭中，归零电流...")
        try:
            current = self.power_controller.target_current
            while current > 0:
                current = max(0, current - 0.1)
                self.power_controller.set_voltage_current(self.power_controller.max_voltage, current)
                print(f"当前电流归零中: {current:.2f} A")
                time.sleep(1)
            self.power_controller.turn_off()
            print("电源已关闭")

            # 保存历史记录，使用用户输入的实验时刻
            with open(HISTORY_FILE, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([self.molecule_name, self.experiment_time, f"{self.power_controller.target_current:.2f}"])

        except Exception as e:
            print(f"关闭电源时出错: {e}")
        finally:
            self.power_controller.close()
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        molecule_dialog = MoleculeInputDialog()
        if molecule_dialog.exec_() == QDialog.Accepted:
            molecule_name, experiment_time = molecule_dialog.get_inputs()
            print(f"分子: {molecule_name}, 实验时刻: {experiment_time}")

            panel = ControlPanel(molecule_name=molecule_name, experiment_time=experiment_time)
            panel.show()
            sys.exit(app.exec_())