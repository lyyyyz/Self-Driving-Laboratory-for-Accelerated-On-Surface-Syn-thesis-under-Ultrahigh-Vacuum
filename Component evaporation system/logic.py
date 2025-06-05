from collections import deque
import time
from PyQt5.QtWidgets import QMessageBox

class EvaporationLogic:
    def __init__(self, power_controller, parent_widget=None):
        """
        初始化蒸发控制逻辑
        :param power_controller: 电源控制器实例，用于调整电流
        :param parent_widget: 用于显示弹窗的主窗口组件
        """
        self.rate_data = deque(maxlen=12)  # 每分钟存储 12 个速率数据（5s 一个数据）
        self.minute_average_rates = deque(maxlen=20)  # 存储最近 20 分钟的平均速率
        self.power_controller = power_controller
        self.parent_widget = parent_widget  # 保存主窗口引用
        self.start_time = time.time()  # 记录开始时间
        self.logic_started = False  # 是否开始逻辑计算
        self.current_group = []  # 当前组数据
        self.previous_group = None  # 上一组数据
        self.adjustment_delay = 0  # 调整后的等待时间（单位：分钟）
        self.last_adjustment_time = None  # 上一次电流调整的时间
        self.rate_within_range = False  # 标志，表示蒸发速率是否在合理范围内

    def add_rate(self, rate):
        if not self.logic_started:
            elapsed_time = time.time() - self.start_time
            if elapsed_time >= 240:
                self.logic_started = True
                print("逻辑计算已启动")
            else:
                print(f"逻辑未启动，剩余时间: {240 - elapsed_time:.1f} 秒")
                return

        if self.last_adjustment_time:
            elapsed_since_adjustment = time.time() - self.last_adjustment_time
            if elapsed_since_adjustment < 180:
                print(f"电流调整后延迟中，剩余: {180 - elapsed_since_adjustment:.1f} 秒")
                return

        self.rate_data.append(rate)

        if len(self.rate_data) == 12:
            average_rate = sum(self.rate_data) / len(self.rate_data)
            self.minute_average_rates.append(average_rate)
            self.rate_data.clear()
            print(f"1 分钟平均速率: {average_rate:.2f}")
            print(f"最近 20 分钟速率: {list(self.minute_average_rates)}")

            self._update_evaporation_rate_analysis()

    def _update_evaporation_rate_analysis(self):
        self.current_group.append(self.minute_average_rates[-1])
        if len(self.current_group) < 5:
            return

        current_group_avg = sum(self.current_group) / len(self.current_group)
        print(f"当前组平均速率: {current_group_avg:.2f}")

        if current_group_avg < 0.5:
            self._adjust_current(0.02)
            print("速率过低，提升电流 0.1A")
            self.rate_within_range = False
        elif 0.5 <= current_group_avg < 0.7:
            self._adjust_current(0.01)
            print("速率过高，提升电流 0.1A")
            self.rate_within_range = False
        elif current_group_avg > 2.5:
            self._adjust_current(-0.1)
            print("速率过高，降低电流 0.5A")
            self.rate_within_range = False
        else:
            print("蒸发速率在合理范围内")
            self.rate_within_range = True

        if self.rate_within_range:
            self._update_stability_analysis()

        self.current_group = []

    def _update_stability_analysis(self):
        if self.previous_group is None:
            self.previous_group = self.current_group
            return

        current_group_avg = sum(self.current_group) / len(self.current_group)
        previous_group_avg = sum(self.previous_group) / len(self.previous_group)
        print(f"当前组平均速率: {current_group_avg:.2f}, 上一组平均速率: {previous_group_avg:.2f}")

        if abs(current_group_avg - previous_group_avg) > 0.3:
            if current_group_avg > previous_group_avg:
                self._adjust_current(-0.02)
                print("组间速率变化过大，降低电流 0.02A")
            else:
                self._adjust_current(0.02)
                print("组间速率变化过大，提升电流 0.02A")
            self.adjustment_delay = 4
        else:
            print("组间速率稳定，无需调整")
            self._show_success_message()

        self.previous_group = self.current_group
        self.current_group = []

    def _adjust_current(self, delta):
        current = self.power_controller.read_current()
        if current is None:
            current = self.power_controller.target_current
        new_current = current + delta
        if new_current < 0:
            new_current = 0
        if new_current > self.power_controller.max_current_limit:
            new_current = self.power_controller.max_current_limit
            print(f"调整的电流超出最大限制，设置为最大电流 {self.power_controller.max_current_limit:.2f} A")
        self.power_controller.set_voltage_current(self.power_controller.max_voltage, new_current)
        print(f"电流调整至: {new_current:.2f} A")
        self.last_adjustment_time = time.time()

    def _show_success_message(self):
        if self.parent_widget:
            current = self.power_controller.read_current()
            msg = QMessageBox(self.parent_widget)
            msg.setWindowTitle("蒸发完成")
            msg.setText(f"蒸发稳定，当前电流为: {current:.2f} A")
            msg.setIcon(QMessageBox.Information)
            msg.exec_()

    def get_minute_averages(self):
        return list(self.minute_average_rates)

