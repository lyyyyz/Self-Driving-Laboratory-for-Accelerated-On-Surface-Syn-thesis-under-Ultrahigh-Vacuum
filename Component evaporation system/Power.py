import pyvisa
import time

class PowerController:
    def __init__(self, resource_name):
        """
        初始化电源控制器
        :param resource_name: 设备资源字符串 (例如 'USB0::0x2EC7::0x320C::123456::INSTR')
        """
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        self.resource_name = resource_name
        self.target_current = 0.0  # 目标电流
        self.max_voltage = 0.0  # 最大电压
        self.max_current_limit = 0.0  # 最大电流限制

    def connect(self):
        """连接到电源设备"""
        try:
            self.instrument = self.rm.open_resource(self.resource_name)
            print(f"已连接到设备: {self.resource_name}")
        except Exception as e:
            print(f"无法连接到设备: {e}")
            raise

    def initialize(self):
        """初始化设备为远程控制模式"""
        if self.instrument:
            self.instrument.write('SYST:REM')
            print("设备已设置为远程控制模式")

    def set_voltage_current(self, voltage, current):
        """
        设置输出电压和电流
        :param voltage: 目标电压 (V)
        :param current: 目标电流 (A)
        """
        if self.instrument:
            # 如果当前电流超出最大电流限制，则限制到最大值
            if current > self.max_current_limit:
                current = self.max_current_limit
                print(f"警告: 电流超出最大限制，调整为最大电流 {self.max_current_limit:.2f} A")
            self.instrument.write(f'VOLT {voltage}')
            self.instrument.write(f'CURR {current}')
            self.target_current = current
            self.max_voltage = voltage
            print(f"设置电压: {voltage} V, 设置电流: {current:.2f} A")

    def set_max_current_limit(self, max_current):
        """
        设置最大电流限制
        :param max_current: 最大允许电流 (A)
        """
        self.max_current_limit = max_current
        print(f"设置最大电流限制: {self.max_current_limit:.2f} A")

    def gradual_current_increase(self, max_current, step=0.05):
        """
        以 0.05A/s 的速率逐步增加电流到目标值
        :param max_current: 目标电流 (A)
        :param step: 每步增加的电流值 (A)，默认 0.05A
        """
        if self.instrument:
            current = 0
            self.instrument.write('OUTP ON')  # 打开电源输出
            while current < max_current:
                current = min(current + step, max_current, self.max_current_limit)
                self.set_voltage_current(self.max_voltage, current)
                time.sleep(1)  # 每秒增加一次电流

    def read_current(self):
        """
        读取当前电流
        :return: 当前实际电流 (A)
        """
        if self.instrument:
            try:
                current = float(self.instrument.query('MEAS:CURR?'))
                print(f"读取当前电流: {current:.2f} A")
                return current
            except Exception as e:
                print(f"读取电流失败: {e}")
                return None
        return None

    def turn_off(self):
        """关闭电源输出"""
        if self.instrument:
            self.instrument.write('OUTP OFF')
            print("电源输出已关闭")

    def close(self):
        """释放资源"""
        if self.instrument:
            self.instrument.close()
            print("设备已关闭")
        self.rm.close()
        print("资源管理器已释放")
