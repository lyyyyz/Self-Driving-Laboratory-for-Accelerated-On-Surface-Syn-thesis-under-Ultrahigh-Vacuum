from PyQt5.QtCore import QThread, pyqtSignal
import serial
import time

class QCMDataCollector(QThread):
    thickness_signal = pyqtSignal(float)  # 膜厚信号
    rate_signal = pyqtSignal(float)      # 速率信号
    frequency_signal = pyqtSignal(str)   # 频率信号

    def __init__(self):
        super().__init__()
        self.ser = None  # 串口对象
        self.port = 'COM6'  # 串口号
        self.baudrate = 19200  # 波特率
        self.timeout = 1  # 读取超时
        self.setup_serial()

    def setup_serial(self):
        """初始化串口"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"串口 {self.port} 已打开.")
        except serial.SerialException as e:
            print(f"无法打开串口: {e}")

    def run(self):
        """数据采集线程"""
        command = '!$P1Z\x11'  # 使用 ASCII 17（0x11）作为命令示例
        thickness_history = []  # 用于存储膜厚数据
        
        while True:
            response = self.send_raw_command(command)  # 读取串口数据
            if response:
                frequency = self.extract_frequency(response)
                if frequency:
                    self.frequency_signal.emit(frequency)  # 发射频率信号
                    
                    current_thickness = self.calculate_thickness(frequency)
                    if current_thickness is not None:
                        thickness_history.append(current_thickness)
                        
                        # 更新速率
                        if len(thickness_history) > 12:
                            thickness_history.pop(0)  # 保持最多12个数据点
                        if len(thickness_history) == 12:
                            rate = self.calculate_rate(thickness_history)
                            self.rate_signal.emit(rate)  # 发射速率信号
                        self.thickness_signal.emit(current_thickness)  # 发射膜厚信号

            # 添加适当的延时，避免占用过多CPU资源
            time.sleep(5)

    def send_raw_command(self, command):
        """发送命令并返回响应"""
        command_bytes = command.encode('ascii', 'ignore')  # 使用 ASCII 编码
        self.ser.write(command_bytes)  # 发送命令
        time.sleep(0.5)  # 等待500毫秒

        response = self.ser.read(self.ser.in_waiting)  # 获取响应
        if response:
            return response.decode('ascii', 'ignore')
        return None

    def extract_frequency(self, data):
        """从数据中提取频率"""
        start_index = data.find('/A') + 2
        if start_index > 1:
            end_index = len(data)
            for i in range(start_index, len(data)):
                if not data[i].isdigit() and data[i] != '.':
                    end_index = i
                    break
            return data[start_index:end_index].strip()
        return None

    def calculate_thickness(self, frequency):
        """根据频率计算膜厚"""
        try:
            freq_value = float(frequency)  # 转换为浮动频率值
            S = 4.407e13  # Hz/Å 常数
            thickness = S / freq_value  # 膜厚公式
            return thickness
        except ValueError:
            return None

    def calculate_rate(self, thickness_history):
        """计算速率"""
        if len(thickness_history) >= 2:
            rate = thickness_history[-1] - thickness_history[0]  # 膜厚差
            return rate
        return 0.0

    def close(self):
        """关闭串口"""
        if self.ser:
            self.ser.close()
            print("串口已关闭.")
