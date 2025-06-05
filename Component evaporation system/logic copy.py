from collections import deque
import time

class EvaporationLogic:
    def __init__(self, power_controller):
        """
        初始化蒸发控制逻辑
        :param power_controller: 电源控制器实例，用于调整电流
        """
        self.rate_data = deque(maxlen=12)  # 每分钟存储 12 个速率数据（5s 一个数据）
        self.minute_average_rates = deque(maxlen=20)  # 存储最近 20 分钟的平均速率
        self.power_controller = power_controller
        self.start_time = time.time()  # 记录开始时间
        self.logic_started = False  # 是否开始逻辑计算
        self.current_group = []  # 当前组数据
        self.previous_group = None  # 上一组数据
        self.adjustment_delay = 0  # 调整后的等待时间（单位：分钟）
        self.last_adjustment_time = None  # 上一次电流调整的时间
        self.rate_within_range = False  # 标志，表示蒸发速率是否在合理范围内

    def add_rate(self, rate):
        """
        添加新的蒸发速率数据
        :param rate: 当前速率
        """
        if not self.logic_started:
            # 等待 4 分钟后启动逻辑
            elapsed_time = time.time() - self.start_time
            if elapsed_time >= 240:  # 4 分钟 = 240 秒
                self.logic_started = True
                print("逻辑计算已启动")
            else:
                print(f"逻辑未启动，剩余时间: {240 - elapsed_time:.1f} 秒")
                return

        # 检查是否处于调整延迟期
        if self.last_adjustment_time:
            elapsed_since_adjustment = time.time() - self.last_adjustment_time
            if elapsed_since_adjustment < 180:  # 等待 3 分钟
                print(f"电流调整后延迟中，剩余: {180 - elapsed_since_adjustment:.1f} 秒")
                return

        # 添加速率数据
        self.rate_data.append(rate)

        # 如果收集满 12 个速率数据，计算平均值并存储
        if len(self.rate_data) == 12:
            average_rate = sum(self.rate_data) / len(self.rate_data)
            self.minute_average_rates.append(average_rate)
            self.rate_data.clear()  # 清空速率队列
            print(f"1 分钟平均速率: {average_rate:.2f}")
            print(f"最近 20 分钟速率: {list(self.minute_average_rates)}")

            # 更新蒸发速率分析（步骤 2）
            self._update_evaporation_rate_analysis()

    def _update_evaporation_rate_analysis(self):
        """
        分析当前蒸发速率范围（步骤 2）
        """
        # 构建当前组
        self.current_group.append(self.minute_average_rates[-1])
        if len(self.current_group) < 5:
            return  # 当前组未满 5 分钟，等待更多数据

        # 处理当前组数据
        current_group_avg = sum(self.current_group) / len(self.current_group)
        print(f"当前组平均速率: {current_group_avg:.2f}")

        # 电流调整逻辑
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
            self.rate_within_range = True  # 速率在合理范围内后进入稳定性分析

        # 如果蒸发速率分析通过，则进入稳定性分析
        if self.rate_within_range:
            self._update_stability_analysis()

        # 清空当前组，重新收集数据
        self.current_group = []

    def _update_stability_analysis(self):
        """
        分析蒸发速率的稳定性（步骤 3）
        """
        # 如果没有上一组，直接保存当前组
        if self.previous_group is None:
            self.previous_group = self.current_group
            return

        # 比较当前组与上一组的稳定性
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
            self.adjustment_delay = 4  # 设置 4 分钟延迟
        else:
            print("组间速率稳定，无需调整")

        # 更新组状态
        self.previous_group = self.current_group
        self.current_group = []

    def _adjust_current(self, delta):
        """
        调整电流
        :param delta: 电流变化值（正负表示增减）
        """
        # 读取当前实际电流
        current = self.power_controller.read_current()
        if current is None:
            current = self.power_controller.target_current  # 如果读取失败，使用目标电流
        new_current = current + delta  # 基于实际电流调整
        if new_current < 0:
            new_current = 0  # 确保电流不为负值
        if new_current > self.power_controller.max_current_limit:
            new_current = self.power_controller.max_current_limit  # 限制电流到最大值
            print(f"调整的电流超出最大限制，设置为最大电流 {self.power_controller.max_current_limit:.2f} A")
        self.power_controller.set_voltage_current(self.power_controller.max_voltage, new_current)
        print(f"电流调整至: {new_current:.2f} A")

        # 记录调整时间
        self.last_adjustment_time = time.time()

    def get_minute_averages(self):
        """
        获取所有已计算的每分钟平均速率
        :return: 最近 20 分钟平均速率列表
        """
        return list(self.minute_average_rates)
