# log.py
import datetime

def log_to_file(log_filename, data):
    with open(log_filename, 'a') as file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {data}\n")

# 添加一个全局变量来存储上一次记录的时间
last_log_time = None

def log_ai_computation(log_filename, current_value, output, voltage):
    global last_log_time
    current_time = datetime.datetime.now()
    
    # 计算时间间隔
    if last_log_time is not None:
        time_interval = (current_time - last_log_time).total_seconds()
    else:
        time_interval = 0  # 第一次记录时没有前一个时间
    
    # 更新上一次记录的时间
    last_log_time = current_time

    # 判断 voltage 的类型并格式化
    if isinstance(voltage, str):
        voltage_str = voltage  # 如果是字符串，直接使用
    else:
        voltage_str = f"{voltage:.3f}"  # 如果是数值，保留三位小数

    log_data = (
        f"Current Value: {current_value:.2f}, "
        f"Output: {output:.3f}, "
        f"Voltage: {voltage_str}, "
        f"Time Interval: {time_interval:.2f} s"
    )
    log_to_file(log_filename, log_data)
