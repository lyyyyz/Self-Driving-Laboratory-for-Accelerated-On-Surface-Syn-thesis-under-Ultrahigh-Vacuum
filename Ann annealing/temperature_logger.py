import os
import time
import csv  # 新增导入 csv 模块
from datetime import datetime

class TemperatureLogger:
    def __init__(self, filename_prefix="anneal", header_info=None):
        # 创建日志文件夹路径
        log_dir = os.path.join(os.path.dirname(__file__), 'temperature_log')
        os.makedirs(log_dir, exist_ok=True)  # 如果文件夹不存在则创建

        # 动态生成文件名，包含时间戳，文件扩展名改为 .csv
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filename = os.path.join(log_dir, f"{filename_prefix}_{current_time}.csv")

        # 写入 CSV 文件头，先写入自定义标题信息（如果有），再写入标准字段行
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            if header_info is not None:
                writer.writerow([header_info])
            writer.writerow(['Timestamp', 'Temperature', 'Output', 'Voltage'])

        self.last_temp = None
        self.last_time = None
        self.stop_logging = False  # 用于控制日志记录停止

    def log_temperature(self, temperature, output, voltage):
        # 获取当前时间，作为日志记录的时间戳
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 将数据写入 CSV 文件，每次记录一行
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_time, f"{temperature:.2f}", f"{output:.2f}", voltage])

        self.last_temp = temperature
        self.last_time = time.time()

    def start_logging(self, temperature_cb, output_cb, voltage_cb, interval=1):
        """使用回调函数获取最新温度、电流和电压信息，并以 CSV 形式记录"""
        try:
            while not self.stop_logging:
                # 调用回调函数获取最新值
                current_temperature = temperature_cb() if callable(temperature_cb) else temperature_cb
                current_output = output_cb() if callable(output_cb) else output_cb
                current_voltage = voltage_cb() if callable(voltage_cb) else voltage_cb

                # 判断 current_voltage 的类型并进行格式化处理
                if isinstance(current_voltage, str):
                    voltage_str = current_voltage
                else:
                    voltage_str = f"{current_voltage:.3f}"

                if current_temperature is not None:
                    self.log_temperature(current_temperature, current_output, voltage_str)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Logging stopped by user.")

    def stop(self):
        """停止日志记录"""
        self.stop_logging = True  # 设置标志位为 True，以停止日志记录
