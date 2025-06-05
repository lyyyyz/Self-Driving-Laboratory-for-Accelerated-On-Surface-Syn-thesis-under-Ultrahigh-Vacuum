import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
import control
import temperature
from AIPredict import AI_Controller
from log import log_ai_computation
from table import ControlPanel
from temperature_logger import TemperatureLogger  # 导入温度记录器
import numpy as np

class PowerControlPanel(QWidget):
    def __init__(self, auto_input=False, auto_voltage=25.0, auto_current=0.0, auto_temperature=0.0, auto_time=0.0, auto_heating_rate=1.0):
        super().__init__()

        # 自动测试模式标志
        self.auto_test_mode = '--auto-input' in sys.argv

        # 初始化线程为 None
        self.control_thread = None

        # 创建电源控制和温度传感器实例
        self.power_control = control.PowerControl()
        self.temperature_sensor = temperature.TemperatureSensor()

        # 初始化温度记录器和记录线程
        self.temperature_logger = None
        self.temperature_thread = None  # 记录温度的线程

        # 初始化参数
        self.voltage = auto_voltage  # 默认电压为 25V
        self.target_current = auto_current
        self.target_temperature = auto_temperature  # 实际温度设定值
        self.current_current = 0.0
        self.current_voltage = 0.0
        self.current_temperature = 0.0
        self.stop_requested = False

        # 手动调电流相关标志：
        self.adjust_requested = False
        self.adjust_target_current = 0.0
        # 用于只打印一次"电流已调整到目标值"：
        self.has_printed_reached_current = False

        self.exit_immediately = False  # 新增标志，表示是否直接退出程序，不做电流清零操作

        self.heating_time = auto_time
        self.heating_start_time = None

        # 初始化速率变量
        self.heating_rate = auto_heating_rate
        self.max_change_rate = 0.05 # 电流最大变化率

        self.switching_mode = False  # 新增标志，表示当前是否在切换控制模式

        # 创建 AI 控制器实例
        self.ai = None

        # 记录温度数据的变量
        self.last_valid_temperature = None      # 上一次有效温度（经过校正后的实际温度）
        self.last_valid_timestamp = None        # 上一次读取温度的时间戳
        self.last_temperature_rate = 0.0          # 最近的温度上升速率，单位 °C/s

        # 创建 UI
        self.control_panel = ControlPanel(
            self.start_control,
            self.request_stop_control,
            self.request_adjust_current,  
            pause_callback=self.pause_control  # 添加暂停回调
        )
        self.init_ui()

        # 启动温度读取定时器
        self.start_temperature_update()

        # 根据标志决定是否自动输入参数
        if auto_input:
            QTimer.singleShot(1000, self.auto_set_parameters)  # 延迟1秒后自动设置参数

        # 检查是否处于恢复模式
        self.recovery_mode = '--recovery-mode' in sys.argv
        if self.recovery_mode:
            print("运行恢复模式：将通过控制循环执行关闭操作")
            QTimer.singleShot(1000, self.start_recovery_control)  # 延迟1秒后启动恢复控制

    def auto_set_parameters(self):
        """自动设置参数, 我跑AI的时候用的"""
        self.control_panel.voltage_input.setText(str(self.voltage))  # 设置电压
        self.control_panel.current_input.setText(str(self.target_current))   # 设置电流
        self.control_panel.temperature_input.setText(str(self.target_temperature))  # 设置温度
        self.control_panel.time_input.setText(str(self.heating_time))  # 设置时间

        # 自动启动控制
        self.start_control()

    def start_temperature_logging(self):
        """启动温度记录线程，同时记录电流和电压"""
        if self.temperature_logger is None or self.temperature_thread is None:
            header_info = (f"# Setpoint: {self.target_temperature}, Heating Rate: {self.heating_rate}, "
                           f"Called from main_aototest: {'--auto-input' in sys.argv}")
            self.temperature_logger = TemperatureLogger("temperature_log", header_info)
            self.temperature_thread = threading.Thread(
                target=self.temperature_logger.start_logging,
                args=(self.get_current_temperature, self.get_current_current, self.get_current_voltage, 1)
            )
            self.temperature_thread.start()

    def stop_temperature_logging(self):
        """停止温度记录线程"""
        if self.temperature_logger is not None:
            self.temperature_logger.stop()  # 请求停止记录器
            if self.temperature_thread is not None:
                self.temperature_thread.join()
                print("Temperature logging has stopped.")
            self.temperature_logger = None
            self.temperature_thread = None

    def get_current_temperature(self):
        """返回当前记录的温度值"""
        return self.current_temperature

    def get_current_current(self):
        return self.current_current

    def get_current_voltage(self):
        return self.current_voltage

    def closeEvent(self, event):
        """确保在关闭时正确关闭所有线程和传感器"""
        self.request_stop_control()
        if self.control_thread is not None:
            self.control_thread.join()

        # 停止温度记录
        self.stop_temperature_logging()

        # 关闭温度传感器
        self.temperature_sensor.close()
        event.accept()

    def init_ui(self):
        """初始化 UI 布局"""
        self.setWindowTitle('Power control panel')
        layout = QVBoxLayout()
        layout.addWidget(self.control_panel)
        self.setLayout(layout)
    
    def start_temperature_update(self):
        """启动温度更新定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_temperature)
        self.timer.start(1000)

    def update_temperature(self):
        """更新当前温度显示，并更新实例属性self.current_temperature"""
        infrared_temperature = self.temperature_sensor.get_temperature()
        if infrared_temperature is not None:
            actual_temperature = infrared_temperature * 0.88 + 9.87
            # 更新保存的温度数据
            self.current_temperature = actual_temperature
            self.control_panel.update_temperature_display(
                actual_temperature, infrared_temperature,
                self.current_current, self.current_voltage
            )
        else:
            self.control_panel.infrared_data.setText('Read failed')

    def start_control(self, heating_rate=None):
        """
        获取用户输入并启动控制逻辑。
        如果 target_temperature、heating_time 或加热速率的输入为空，则进入手动控制模式，
        仅基于电压和电流设置电源，不进行自动温度控制和 AI 调节。
        """
        # 如果已有控制线程在运行，先停止它
        if self.control_thread is not None and self.control_thread.is_alive():
            print("Stopping current control before starting new one...")
            self.switching_mode = True  # 表示这是一次切换操作，不希望将电流降到0
            self.stop_requested = True  # 请求停止当前控制
            self.control_thread.join()  # 等待线程结束
            self.stop_temperature_logging()  # 停止温度记录
            
            # 重置相关变量
            self.stop_requested = False
            self.control_thread = None
            self.heating_start_time = None
            self.last_valid_temperature = None
            self.last_valid_timestamp = None
            self.last_temperature_rate = 0.0
            
            # 重置手动调电流模式的标志
            self.adjust_requested = False
            self.has_printed_reached_current = False
            
            # 确保电源输出停止
            print("Switching mode: preserving current output state.")
            time.sleep(1)  # 短暂延时确保所有操作完成
        
        # 检查温度、时间和加热速率输入是否为空
        if (not self.control_panel.temperature_input.text().strip() or 
            not self.control_panel.time_input.text().strip() or 
            not self.control_panel.heating_rate_input.text().strip()):
            
            try:
                self.voltage = float(self.control_panel.voltage_input.text())
                self.target_current = float(self.control_panel.current_input.text())
            except ValueError:
                print("Please enter valid voltage and current values.")
                return
            
            print("Entering manual control mode (partial input missing, skipping auto parameter configuration).")
            self.power_control.set_power(self.voltage, self.target_current, 0)
            self.power_control.start_output()
            
            # 启动手动调节线程
            self.stop_requested = False
            self.control_thread = threading.Thread(target=self.manual_control_loop)
            self.control_thread.start()
            
            return
        
        # 否则，按照常规方式读取所有参数
        try:
            self.voltage = float(self.control_panel.voltage_input.text())
            self.target_current = float(self.control_panel.current_input.text())
            self.target_temperature = float(self.control_panel.temperature_input.text())
            self.heating_time = float(self.control_panel.time_input.text())

        except ValueError:
            print("请输入有效的数字值")
            return
        
        # 获取用户输入的加热速率
        if heating_rate is not None:
            self.heating_rate = heating_rate
        else:
            try:
                self.heating_rate = float(self.control_panel.heating_rate_input.text())
            except ValueError:
                print("请输入有效的加热速率")
                return

        # 计算红外目标温度设定值
        infrared_temperature_setpoint = (self.target_temperature - 9.87) / 0.88

        # 在 ai_log.txt 中记录 setpoint 和调用信息
        with open("ai_log.txt", "a") as log_file:
            log_file.write(f"# Setpoint: {infrared_temperature_setpoint}, Heating Rate: {self.heating_rate}, Called from main_aototest: {'--auto-input' in sys.argv}\n")

        # 显示计算出的红外目标温度
        self.control_panel.set_infrared_target_temperature_display(infrared_temperature_setpoint)

        if infrared_temperature_setpoint > 590:
            # 如果目标红外温度超过 590°C，红外失灵，选择直接阶梯升温
            self.control_thread = threading.Thread(target=self.high_temperature_control_loop)
        else:
            # 如果目标红外温度低于 590°C，使用 AI 控制
            min_current = 0.0
            max_current = self.target_current

            # 初始化 AI 控制器
            self.ai = AI_Controller(
                setpoint=infrared_temperature_setpoint,
                output_limits=(min_current, max_current),
                log_function=lambda *args: log_ai_computation("ai_log.txt", *args),
                max_change_rate=self.max_change_rate,
                heating_rate=self.heating_rate
            )
            self.control_thread = threading.Thread(target=self.control_loop)

        # 重置停止请求标志
        self.stop_requested = False

        # 重置切换标志（新控制启动后）
        self.switching_mode = False

        # 启动控制线程
        self.control_thread.start()

        # 启动温度记录
        self.start_temperature_logging()

    def request_stop_control(self):
        """请求停止控制"""
        self.stop_requested = True
        self.stop_temperature_logging()  # 停止温度记录

    def stop_control(self):
        """停止电源控制。如果 preserve_current 为 True，则保留当前电流，不进行逐步降低。"""
        # 逐步降低电流
        while self.current_current > 0:
            self.current_current -= self.max_change_rate * 2  # 每次减少的电流量
            self.current_current = max(self.current_current, 0)  # 确保电流不低于0
            self.power_control.set_power(self.voltage, self.current_current, 0)
            time.sleep(1)  # 每次减少后等待
        # 停止电源输出
        self.power_control.stop_output()

        with open("ai_log.txt", "a") as log_file:
            log_file.write("\n")  # 写入一个空行
        print("Power control has been stopped.")

    def request_adjust_current(self, target_current):
        """
        当收到调电流请求时，如果控制线程未启动，则先启动控制。
        同时将手动覆盖标志置为 True，确保控制循环优先执行手动调整逻辑。
        """
        if self.control_thread is None or not self.control_thread.is_alive():
            print("Manual control thread not running, starting manual control mode.")
            self.start_control()  # 启动控制线程

        self.adjust_requested = True
        self.adjust_target_current = target_current
        self.has_printed_reached_current = False  # 重置标志
        print(f"[request_adjust_current] Current adjustment requested to {target_current} A")

    def handle_manual_adjustment(self):
        """
        手动调电流处理逻辑：
        不依赖温度读取结果，直接根据用户设定目标调节当前电流。
        """
        diff = self.adjust_target_current - self.current_current
        step_size = self.max_change_rate  # 每步调节的电流量

        # 如果当前电流与目标电流差距较大，则按步长调整
        if abs(diff) > step_size:
            old_current = self.current_current
            if diff > 0:
                self.current_current += step_size
            else:
                self.current_current -= step_size
            self.power_control.set_power(self.voltage, self.current_current, 0)
        else:
            # 差距较小时直接设置为目标电流
            self.current_current = self.adjust_target_current
            self.power_control.set_power(self.voltage, self.current_current, 0)
            if not self.has_printed_reached_current:
                print("Successfully adjusted current to target value.")
                self.has_printed_reached_current = True

    def control_loop(self):
        """主控制循环（在后台线程中运行，不阻塞 UI）"""
        # 初始化当前电流
        self.current_current = self.power_control.get_current()
        self.power_control.stop_requested = False

        # 设置初始电压并开启电源输出
        self.power_control.set_power(self.voltage, self.current_current, 0)
        self.power_control.start_output()

        '''
        # 只在自动测试模式（main_aototest.py调用）下检查初始电流
        if '--auto-input' in sys.argv and self.current_current != 0:
            self.stop_requested = True
            print("Initial current is non-zero; invoking stop_control.")
            self.stop_control()
            self.stop_temperature_logging()  # 停止温度日志记录
            print("Shutting down program (initial current non-zero).")
            QApplication.quit()  # 使用 QApplication.quit() 退出程序
            return
        '''

        failed_reads = 0
        max_failed_reads = 10
        loop_counter = 0  # 循环计数器

        ### 引入最大运行时长 ###
        start_time = time.time()
        max_duration = float('inf')  # 你可以改成别的值，或做成可调

        while not self.stop_requested:
            # 每隔10次循环获取一次电压
            if loop_counter % 10 == 0:
                self.current_voltage = self.power_control.get_voltage()
            else:
                self.current_voltage = "Not measured"

            # 获取温度数据（用于更新显示及后续处理）
            infrared_temperature = self.temperature_sensor.get_temperature()
            if infrared_temperature is not None:
                failed_reads = 0
                actual_temperature = infrared_temperature * 0.88 + 9.87
                self.current_temperature = actual_temperature
                self.control_panel.update_temperature_display(
                    actual_temperature, infrared_temperature,
                    self.current_current, self.current_voltage
                )
                # 更新温度上升速率记录
                current_time = time.time()
                if self.last_valid_temperature is not None and self.last_valid_timestamp is not None:
                    dt = current_time - self.last_valid_timestamp
                    if dt > 0:
                        self.last_temperature_rate = (infrared_temperature - self.last_valid_temperature) / dt
                self.last_valid_temperature = infrared_temperature
                self.last_valid_timestamp = current_time
                
            else:
                failed_reads += 1
                print(f"Temperature reading failed. *{failed_reads}")

            # 优先判断手动调电流模式，无论温度是否读取成功均执行手动调整
            if self.adjust_requested:
                try:
                    self.heating_time = float(self.control_panel.time_input.text())
                except:
                    self.heating_time = None
                while not self.stop_requested:
                    if self.adjust_requested:
                        # 开启计时
                        if self.heating_start_time is None:
                            self.heating_start_time = time.time()
                        # 更新并检查加热时间
                        if self.heating_start_time is not None and self.heating_time is not None:
                            elapsed_time_heat = time.time() - self.heating_start_time
                            self.control_panel.update_elapsed_time(elapsed_time_heat)
                            if elapsed_time_heat >= self.heating_time:
                                self.stop_requested = True
                                print("Heating duration reached; stopping control.")
                                self.stop_control()
                                self.stop_temperature_logging()
                                if self.auto_test_mode:
                                    QApplication.quit()
                                return
                        self.handle_manual_adjustment()
            else:
                # AI 控制模式
                # 检查是否达到启动加热计时的条件
                if self.heating_start_time is None and actual_temperature >= (self.target_temperature - 5):
                    self.heating_start_time = time.time()
                # 更新并检查加热时间
                if self.heating_start_time is not None:
                    elapsed_time_heat = time.time() - self.heating_start_time
                    self.control_panel.update_elapsed_time(elapsed_time_heat)
                    if elapsed_time_heat >= self.heating_time:
                        self.stop_requested = True
                        print("Heating duration reached; stopping control.")
                        self.stop_control()
                        self.stop_temperature_logging()
                        if self.auto_test_mode:
                            QApplication.quit()
                        return
                if infrared_temperature is not None:
                    # 获取 AI 原始预测值
                    prediction = self.ai.ai_predict(current_value=infrared_temperature)

                    # 速率控制：判断 AI 预测值相对于当前值的变化是否超过最大变化率
                    delta_output = prediction - self.current_current
                    if abs(delta_output) > self.max_change_rate:
                        print(f"Warning: AI prediction change rate exceeded! Adjusting from {prediction} to within ±{self.max_change_rate} of {self.current_current}.")
                        if delta_output > 0:
                            prediction = self.current_current + self.max_change_rate
                        else:
                            prediction = self.current_current - self.max_change_rate

                    # 限制预测输出范围
                    if prediction < self.ai.output_limits[0] or prediction > self.ai.output_limits[1]:
                        print(f"Warning: Output {prediction} is out of limits! Adjusting to limits {self.ai.output_limits}.")
                        prediction = max(self.ai.output_limits[0], min(prediction, self.ai.output_limits[1]))

                    self.current_current = prediction
                    self.power_control.set_power(self.voltage, self.current_current, 0)
                    log_ai_computation("ai_log.txt", infrared_temperature, self.current_current, self.current_voltage)
                else:
                    # 当温度读取失败时，利用之前记录的温度上升速率和时间间隔进行虚拟AI控制
                    if self.last_valid_temperature is not None and self.last_valid_timestamp is not None:
                        # 计算自上次有效温度读取后的时间间隔（秒）
                        delta_t = time.time() - self.last_valid_timestamp
                        # 利用温度上升速率预测当前温度
                        predicted_temperature = self.last_valid_temperature + self.last_temperature_rate * delta_t
                        # 使用预测温度作为输入，调用 AI 得到虚拟预测值
                        virtual_predicted = self.ai.ai_predict(current_value=predicted_temperature)
                        # 速率控制
                        diff = virtual_predicted - self.current_current
                        if abs(diff) > self.max_change_rate:
                            print(f"Warning: AI prediction change rate exceeded! Adjusting from {virtual_predicted} to within ±{self.max_change_rate} of {self.current_current}.")
                            virtual_predicted += self.max_change_rate if diff > 0 else -self.max_change_rate
                        # 限制虚拟预测输出范围
                        if virtual_predicted < self.ai.output_limits[0] or virtual_predicted > self.ai.output_limits[1]:
                            print(f"Warning: Virtual prediction {virtual_predicted} is out of limits {self.ai.output_limits}, adjusting to acceptable range.")
                            virtual_predicted = max(self.ai.output_limits[0], min(virtual_predicted, self.ai.output_limits[1]))
                        self.current_current = virtual_predicted
                        self.power_control.set_power(self.voltage, self.current_current, 0)
                        #print(f"Temperature reading failed! Utilizing virtual AI control for adjustment. Predicted temperature: {predicted_temperature:.2f}°C, virtual prediction: {virtual_predicted:.2f} A, current: {self.current_current:.2f} A")
                    else:
                        print("Temperature reading failed and no valid historical temperature data is available; unable to perform virtual AI control.")
                    if failed_reads >= max_failed_reads:
                        print("Multiple consecutive temperature reading failures detected. Please switch to manual control.")
                        self.request_adjust_current(self.current_current)
                        # 调用 ControlPanel 中的弹窗警告函数
                        self.control_panel.show_temperature_failure_warning()
                        failed_reads = 0

            time.sleep(1)
            loop_counter += 1

            # 检查是否超出最大运行时长
            if time.time() - start_time > max_duration:
                print(f"Maximum runtime of {max_duration} seconds reached; stopping control.")
                self.stop_requested = True
                self.stop_temperature_logging()  # 确保温度日志记录停止
                break

        print("Exiting loop and shutting down program.")
        # 如果不是切换模式，则执行完全停止操作
        if not self.switching_mode and not self.exit_immediately:
            self.stop_control()  # 这会逐步降低电流并停止输出
        else:
            with open("ai_log.txt", "a") as log_file:
                log_file.write("\n")  # 写入一个空行
            print("Power control has been stopped.")
            print("Exiting loop: preserving current output.")
        self.stop_temperature_logging()
        if self.auto_test_mode:
            QApplication.quit()

    def high_temperature_control_loop(self):
        """高温控制循环(不使用AI)"""
        self.current_current = 0.0
        self.power_control.stop_requested = False

        self.power_control.set_power(self.voltage, self.current_current, 0)
        self.power_control.start_output()

        while not self.stop_requested:
            infrared_temperature = self.temperature_sensor.get_temperature()
            if infrared_temperature is not None:
                actual_temperature = infrared_temperature * 0.88 + 9.87
                self.control_panel.update_temperature_display(actual_temperature, infrared_temperature, self.current_current, None)

            if self.current_current < self.target_current:
                self.current_current += 0.05
                self.current_current = min(self.current_current, self.target_current)
                self.power_control.set_power(self.voltage, self.current_current, 0)

            time.sleep(1)

        self.stop_control()

    def manual_control_loop(self):
        """仅处理手动调电流请求的简单循环。"""
        try:
            self.heating_time = float(self.control_panel.time_input.text())
        except:
            self.heating_time = None
        while not self.stop_requested:
            if self.adjust_requested:
                # 开启计时
                if self.heating_start_time is None:
                    self.heating_start_time = time.time()
                # 更新并检查加热时间
                if self.heating_start_time is not None and self.heating_time is not None:
                    elapsed_time_heat = time.time() - self.heating_start_time
                    self.control_panel.update_elapsed_time(elapsed_time_heat)
                    if elapsed_time_heat >= self.heating_time:
                        self.stop_requested = True
                        print("Heating duration reached; stopping control.")
                        self.stop_control()
                        self.stop_temperature_logging()
                        if self.auto_test_mode:
                            QApplication.quit()
                        return
                self.handle_manual_adjustment()
            time.sleep(1)
        
        print("Exiting loop and shutting down program.")
        # 如果不是切换模式，则执行完全停止操作
        if not self.switching_mode and not self.exit_immediately:
            self.stop_control()  # 这会逐步降低电流并停止输出
        else:
            with open("ai_log.txt", "a") as log_file:
                log_file.write("\n")  # 写入一个空行
            print("Power control has been stopped.")
            print("Exiting loop: preserving current output.")
        self.stop_temperature_logging()
        if self.auto_test_mode:
            QApplication.quit()
            
    def pause_control(self):
        """暂停控制并退出程序，直接终止线程，不修改电流值"""
        print("Pausing control and exiting program.")
        # 设置直接退出标志
        self.exit_immediately = True
        # 请求停止控制
        self.stop_requested = True
        # 等待控制线程结束
        if self.control_thread is not None and self.control_thread.is_alive():
            self.control_thread.join()
        # 停止温度记录线程
        self.stop_temperature_logging()
        # 退出应用
        QApplication.quit()

    def start_recovery_control(self):
        """启动恢复模式的控制循环"""
        # 设置最小参数以启动控制循环
        self.voltage = 25.0
        self.target_current = 0.0
        self.target_temperature = 0.0
        self.heating_time = 0.0
        self.heating_rate = 1.0
        
        # 创建并启动恢复控制线程
        self.stop_requested = False
        self.control_thread = threading.Thread(target=self.recovery_control_loop)
        self.control_thread.start()

    def recovery_control_loop(self):
        """恢复模式的控制循环"""
        print("开始恢复模式控制循环")
        
        # 初始化电源通信
        self.current_current = self.power_control.get_current()
        print(f"当前电流: {self.current_current}A")
        
        # 执行关闭操作
        self.stop_control()
        self.stop_temperature_logging()
        
        # 确保电源完全关闭后退出程序
        time.sleep(2)
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 获取命令行参数并初始化 PowerControlPanel
    auto_input = '--auto-input' in sys.argv
    auto_voltage = float(sys.argv[sys.argv.index('--voltage') + 1]) if '--voltage' in sys.argv else 25.0
    auto_current = float(sys.argv[sys.argv.index('--current') + 1]) if '--current' in sys.argv else 0.0
    auto_temperature = float(sys.argv[sys.argv.index('--temperature') + 1]) if '--temperature' in sys.argv else 0.0
    auto_time = float(sys.argv[sys.argv.index('--time') + 1]) if '--time' in sys.argv else 0.0
    auto_heating_rate = float(sys.argv[sys.argv.index('--heating-rate') + 1]) if '--heating-rate' in sys.argv else 1.0

    window = PowerControlPanel(
        auto_input=auto_input,
        auto_voltage=auto_voltage,
        auto_current=auto_current,
        auto_temperature=auto_temperature,
        auto_time=auto_time,
        auto_heating_rate=auto_heating_rate
    )
    window.show()
    
    sys.exit(app.exec_())
