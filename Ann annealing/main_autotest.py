import subprocess
import time
import random
import os
import signal
import sys

def run_program(temperature, is_recovery=False):
    kill_existing_main_ai()  # 确保不会重复运行 main_ai.py

    # 从指定的加热速率中随机选择一个
    heating_rate = random.choice([0.8, 1.0, 1.5])

    try:
        # 构建基本命令参数
        cmd = [
            'python', 'main_ai.py', '--auto-input',
            '--voltage', '25.0',
            '--current', '3.85',
            '--temperature', str(temperature),
            '--time', '200',
            '--heating-rate', str(heating_rate)
        ]

        # 如果是恢复模式，添加恢复标志
        if is_recovery:
            cmd.append('--recovery-mode')

        # 启动程序并等待完成
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=1200)  # 设置超时时间（1200秒 = 20分钟）
            return_code = process.returncode
        except subprocess.TimeoutExpired:
            print(f"main_ai.py 运行超时（{temperature}°C），强制终止进程并进入恢复模式")
            process.kill()  # 终止进程
            run_program(temperature, is_recovery=True)  # 进入恢复模式
            return

        # 检查程序是否正常退出
        if return_code != 0:
            print(f'程序异常退出（返回码：{return_code}），正在进行恢复操作...')
            # 运行恢复程序来关闭电源
            run_program(temperature, is_recovery=True)
            # 等待额外的冷却时间
            print('正在等待额外的冷却时间...')
            time.sleep(300)  # 5分钟额外冷却时间
            # 重新尝试当前温度点
            print(f'重新尝试温度点 {temperature}')
            run_program(temperature)
        
    except Exception as e:
        print(f'发生异常：{e}')
        # 运行恢复程序来关闭电源
        run_program(temperature, is_recovery=True)
        # 等待额外的冷却时间
        print('正在等待额外的冷却时间...')
        time.sleep(300)  # 5分钟额外冷却时间
        # 重新尝试当前温度点
        print(f'重新尝试温度点 {temperature}')
        run_program(temperature)
    
def kill_existing_main_ai():
    """查找并杀掉正在运行的 main_ai.py"""
    try:
        result = subprocess.run(["pgrep", "-f", "main_ai.py"], capture_output=True, text=True)
        pids = result.stdout.strip().split("\n")

        for pid in pids:
            if pid.isdigit():
                print(f"正在终止已有的 main_ai.py 进程: {pid}")
                os.kill(int(pid), signal.SIGTERM)
    except Exception as e:
        print(f"终止 main_ai.py 失败: {e}")

if __name__ == '__main__':
    temp_range = range(150, 451, 15)  # 温度范围定义
    first_temp = temp_range[0]  # 动态获取第一个温度值
    
    # 执行所有温度点
    for temp in temp_range:
        run_program(temp)
        print('正在等待降温')
        time.sleep(300)  # 等待降温
    
    # 最后重新执行第一个温度点
    print(f'重新执行第一个温度点 {first_temp}')
    run_program(first_temp)
    print('实验完成')
