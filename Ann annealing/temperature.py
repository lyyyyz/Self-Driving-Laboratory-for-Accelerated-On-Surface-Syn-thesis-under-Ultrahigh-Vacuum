import serial
import serial.tools.list_ports
import time
from collections import deque

class TemperatureSensor:
    def __init__(self, device_name="USB-SERIAL CH340", baudrate=9600, max_temp_change=10, stability_threshold=5, stable_range=5):
        # 动态查找串口
        port = self.find_serial_port_by_device_name(device_name)
        if port is None:
            print(f"Warning: Device {device_name} not found, enter no temperature sensor mode.")
            self.ser = None
        else:
            self.ser = serial.Serial(port, baudrate)
        self.temp_send = bytes.fromhex('01 03 00 00 00 01 84 0A')
        self.max_temp_change = max_temp_change
        self.stability_threshold = stability_threshold  # 连续稳定读数的数量
        self.stable_range = stable_range  # 稳定范围
        self.last_temp = None
        self.history = deque(maxlen=stability_threshold)  # 用队列记录最近的温度读数

    def find_serial_port_by_device_name(self, device_name):
        """根据设备名称查找串口"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if device_name in port.description:
                return port.device
        return None

    def extract_temperature(self, hex_str):
        try:
            if len(hex_str) >= 10:
                temp_hex = hex_str[6:10]
                temperature = int(temp_hex, 16)

                # 如果是第一次读取温度，直接接受
                if self.last_temp is None:
                    self.last_temp = temperature
                    self.history.append(temperature)
                    return temperature

                # 检查当前温度与上次的跳变是否超出范围
                if abs(temperature - self.last_temp) > self.max_temp_change:
                    print(f"Temperature jump too large: {self.last_temp} -> {temperature}")
                    # 将跳变后的温度添加到历史记录
                    self.history.append(temperature)

                    # 检查历史记录是否稳定
                    if len(self.history) == self.stability_threshold and self.is_stable():
                        self.last_temp = temperature
                        print(f"Stabilized temperature after jump: {temperature}")
                        return temperature
                    return None

                # 如果没有跳变，更新历史记录并返回温度
                self.history.append(temperature)
                self.last_temp = temperature
                return temperature
            else:
                print("Received hex string is too short.")
                return None
        except (ValueError, IndexError) as e:
            print(f"Error extracting temperature: {e}")
            return None

    def is_stable(self):
        """检查历史记录中的温度是否在稳定范围内"""
        if len(self.history) < self.stability_threshold:
            return False
        min_temp = min(self.history)
        max_temp = max(self.history)
        return (max_temp - min_temp) <= self.stable_range

    def get_temperature(self):
        if self.ser is None:
            # 没有连接温度传感器，直接返回None
            return None

        if self.ser.is_open:
            self.ser.write(self.temp_send)
            time.sleep(0.1)

            buffer_data = self.ser.in_waiting
            if buffer_data:
                return_data = self.ser.read(buffer_data)
                return_data_hex = return_data.hex()
                return self.extract_temperature(return_data_hex)
        return None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
