'''
提取、整理数据用于机器学习模型训练
'''
import numpy as np

def process_data(file_path):
    data = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # 读取数据时，保留空行和注释行，用于标示数据间断
    for index, line in enumerate(lines):
        stripped_line = line.strip()

        # 如果是空行或以 # 开头的注释行，标记为 None
        if stripped_line.startswith('#') or not stripped_line:
            data.append(None)
            continue

        parts = stripped_line.split(', ')
        if len(parts) < 4:
            print(f"Skipping line {index} due to unexpected format: {stripped_line}")
            data.append(None)  # 格式不正确的行也作为间断
            continue

        try:
            current_value = float(parts[0].split('Current Value: ')[1])
            output = float(parts[1].split('Output: ')[1])
            voltage = float(parts[2].split('Voltage ')[1])  # 解析 Voltage
            time_interval_str = parts[3].split('Time Interval: ')[1].replace(' s', '').strip()
            time_interval = float(time_interval_str) if time_interval_str else 0.0
            data.append((current_value, output, voltage, time_interval))  # 存储 Voltage
        except (IndexError, ValueError) as e:
            print(f"Error parsing line {index}: {stripped_line} - {e}")
            data.append(None)  # 如果解析出错，也作为间断
            continue

    # 准备输出和未来值的矩阵
    outputs_matrix = []
    future_values_matrix = []

    for i in range(len(data)):
        if data[i] is None:
            # 当前行是空行或注释行，跳过
            continue

        # 获取当前数据点的 output
        current_output = data[i][1]

        # 初始化未来20秒的 Current Value 数据
        future_values = [np.nan] * 20  # 使用 np.nan 代替 None
        time_accumulated_future = 0.0
        times_future = []
        values_future = []

        valid_future = True  # 标记未来数据是否有效

        # 从第 i-1 行开始收集未来数据
        for j in range(i - 1, len(data)):
            if data[j] is None:
                # 在收集过程中遇到间断，当前数据点作废
                valid_future = False
                print(f"Data point at index {i} is invalid due to future interruption at index {j}.")
                break

            time_interval = data[j][3]
            if time_interval <= 0:
                print(f"Data point at index {j} has non-positive time interval: {time_interval}. Skipping future data collection.")
                valid_future = False
                break

            time_accumulated_future += time_interval

            if time_accumulated_future > 20:
                # 超过20秒，停止收集
                break

            times_future.append(time_accumulated_future)
            values_future.append(data[j][0])

        # 检查未来数据是否达到20秒
        if time_accumulated_future < 20:
            valid_future = False
            print(f"Data point at index {i} has insufficient future data: accumulated {time_accumulated_future} s.")

        # 检查未来数据的有效性
        if not valid_future:
            continue  # 数据点作废，不加入矩阵

        # 检查是否有足够的数据进行插值
        if len(times_future) < 1:
            print(f"Insufficient data for interpolation at index {i}.")
            continue

        try:
            # 处理未来20秒 Current Value 的插值
            interp_times_future = times_future  # 已经是递增的
            interp_values_future = values_future
            future_times = np.arange(1, 21, 1)  # 1到20秒的整数时间点
            future_values_interp = np.interp(future_times, interp_times_future, interp_values_future, left=interp_values_future[0], right=interp_values_future[-1])

            for idx, val in enumerate(future_values_interp):
                future_values[idx] = val

            # 添加到各自的矩阵
            future_values_matrix.append(future_values)
            outputs_matrix.append(current_output)
        except Exception as e:
            print(f"Interpolation failed for data point at index {i}: {e}")
            continue

    # 将矩阵转换为 numpy 数组
    outputs_matrix_array = np.array(outputs_matrix).reshape(-1, 1)
    future_values_matrix_array = np.array(future_values_matrix)

    print('outputs_matrix_array shape:', outputs_matrix_array.shape)
    print('future_values_matrix_array shape:', future_values_matrix_array.shape)

    return outputs_matrix_array, future_values_matrix_array

def save_matrix_to_file(outputs_matrix_array, future_values_matrix_array, output_file_path):
    # 保存所有矩阵到文本文件
    with open(output_file_path, 'w') as f:
        f.write("Outputs Matrix:\n")
        np.savetxt(f, outputs_matrix_array, fmt='%.2f')

        f.write("\nFuture Current Values Matrix:\n")
        np.savetxt(f, future_values_matrix_array, fmt='%.2f')
        f.write("\n")

if __name__ == "__main__":
    # 示例用法
    file_path = 'new_experiment_log.txt'
    output_file_path = 'matrix_output.txt'  # 保存到程序所在的文件夹

    # 调用 process_data 函数
    outputs_matrix, future_values_matrix = process_data(file_path)

    # 调用 save_matrix_to_file 函数
    save_matrix_to_file(outputs_matrix, future_values_matrix, output_file_path)

    print('outputs_matrix_length:', len(outputs_matrix), 
          'future_values_matrix_length:', len(future_values_matrix))
    print("Matrices saved to:", output_file_path)
