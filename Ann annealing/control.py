# control.py
import pyvisa
import time

class PowerControl:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource('USB0::0x2EC7::0x320C::804634011797110022::2::INSTR')
        self.stop_requested = False

    def set_power(self, voltage, current, duration):
        try:
            self.instrument.write(f'VOLT {voltage}')
            self.instrument.write(f'CURR {current}')
            # Duration控制可以通过sleep或外部计时控制，但在此方法中不进行时间控制
        except pyvisa.VisaIOError as e:
            print(f"VISA I/O Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def start_output(self):
        self.instrument.write('OUTP ON')

    def stop_output(self):
        self.instrument.write('OUTP OFF')

    def get_voltage(self):
        # 查询设备电压
        try:
            # 发送查询命令
            self.instrument.write("MEAS:VOLT?")

            # 读取返回值
            raw_voltage = self.instrument.read() # 返回的可能是字符串，例如 "12.345\n"
            time.sleep(0.2)

            # 处理返回值
            voltage = float(raw_voltage.strip())  # 去掉换行符并转换为浮点数

        except ValueError:
            print(f"Error: Received invalid voltage value: {raw_voltage}")
            return None

        except Exception as e:
            print(f"Error: {e}")
            return None

        return voltage

    def get_current(self):
        # 查询设备电流
        try:
            # 发送查询命令
            self.instrument.write("MEAS:CURR?")

            # 读取返回值
            raw_current = self.instrument.read()  # 返回的可能是字符串，例如 "1.234\n"
            time.sleep(0.2)

            # 处理返回值
            current = float(raw_current.strip())  # 去掉换行符并转换为浮点数

        except ValueError:
            print(f"Error: Received invalid current value: {raw_current}")
            return None

        except Exception as e:
            print(f"Error: {e}")
            return None

        return current

    def close(self):
        if self.instrument:
            self.instrument.close()
        if self.rm:
            self.rm.close()

