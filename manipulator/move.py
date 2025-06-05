#move.py
import multiprocessing
import time
from ctypes import *
import position
import robot

def process_movement(pipe):
    DAQdll = WinDLL("E:\\AIlab\\manipulator\\python\\Usb_AMC1XE.dll")
    valve_status = 'closed'
    current_position = 0

    while True:
        if pipe.poll():
            data = pipe.recv()

            if data is None:
                print("收到关闭信号，退出程序")
                break

            if data == "STOP":
                DAQdll.AxsStop(0, 0, 0)
                print("急停信号收到，传动轴已停止运动")
                continue

            if data == "UPDATE_VALVE_STATUS_OPEN":
                valve_status = 'open'
                print("阀门状态已从前面板更新为: 打开")
                continue
            elif data == "UPDATE_VALVE_STATUS_CLOSED":
                valve_status = 'closed'
                print("阀门状态已从前面板更新为: 关闭")
                continue

            if data == "OPEN_VALVE":
                robot.valveopen()
                valve_status = 'open'
                pipe.send(('UPDATE_VALVE_STATUS', 'open'))
                print("阀门已打开")
                continue
            elif data == "CLOSE_VALVE":
                robot.valveclose()
                valve_status = 'closed'
                pipe.send(('UPDATE_VALVE_STATUS', 'closed'))
                print("阀门已关闭")
                continue

            if isinstance(data, str):
                if data == "XPOSITION_MOVE_IN":
                    robot.Xposition_move_in()
                    print("进入X轴调整位置")
                    continue
                elif data == "XPOSITION_MOVE_OUT":
                    robot.Xposition_move_out()
                    print("退出X轴调整位置")
                    continue
                elif data == "XPOSITION_TARGET_01MM":
                    robot.Xposition_target_01mm()
                    print("X轴前进1mm")
                    continue
                elif data == "XPOSITION_TARGET_10MM":
                    robot.Xposition_target_10mm()
                    print("X轴后退1mm")
                    continue
                elif data == "YPOSITION_MOVE_IN":
                    robot.Yposition_move_in()
                    print("进入Y轴调整位置")
                    continue
                elif data == "YPOSITION_MOVE_OUT":
                    robot.Yposition_move_out()
                    print("退出Y轴调整位置")
                    continue
                elif data == "YPOSITION_TARGET_01MM":
                    robot.Yposition_target_01mm()
                    print("Y轴前进1mm")
                    continue
                elif data == "YPOSITION_TARGET_10MM":
                    robot.Yposition_target_10mm()
                    print("Y轴后退1mm")
                    continue
                elif current_position == 536:
                    if data == "FAI_GET_IN":
                        robot.fai_get_in()
                        print("进入 FAI 轴调整位置")
                        continue
                    elif data == "FAI_5MOVE135":
                        robot.fai_5move135()
                        print("FAI 从 5 移动到 135")
                        continue
                    elif data == "FAI_135MOVE5":
                        robot.fai_135move5()
                        print("FAI 从 135 移动到 5")
                        continue
                    elif data == "FAI_GET_OUT":
                        robot.fai_get_out()
                        print("退出 FAI 轴调整位置")
                        continue
                else:
                    print(f"当前位置为 {current_position}，无法调整 FAI 轴")

            # 确保 Z 轴、X、Y 和 FAI 的所有参数都在管道中传递
            if isinstance(data, tuple) and len(data) == 10:  # 确保传入 Z、X、Y 和 FAI 的目标位置
                abs_value, sign_value, value1, value2, x_target, y_target, fai_target, current_x, current_y, current_fai = data

                if value1 > 460 > value2 and valve_status == 'closed':
                    robot.valveopen()
                    valve_status = 'open'
                    pipe.send(('UPDATE_VALVE_STATUS', 'open'))
                    print("阀门已打开")

                if value1 > 120 > value2:
                    first_abs_value = abs(120 - value1)
                    move_to_position(120, sign_value, first_abs_value, DAQdll, pipe)
                    
                    # 调整X、Y轴后，更新current_x 和 current_y
                    current_x = adjust_x_position(-8, pipe, current_x)
                    current_y = adjust_y_position(10, pipe, current_y)
                    
                    final_abs_value = abs(120 - value2)
                    move_to_position(value2, sign_value, final_abs_value, DAQdll, pipe)

                elif value1 < 120 < value2:
                    first_abs_value = abs(120 - value1)
                    move_to_position(120, sign_value, first_abs_value, DAQdll, pipe)
                    
                    # 调整X、Y轴后，更新current_x 和 current_y
                    current_x = adjust_x_position(-2, pipe, current_x)
                    current_y = adjust_y_position(6, pipe, current_y)
                    
                    final_abs_value = abs(120 - value2)
                    move_to_position(value2, sign_value, final_abs_value, DAQdll, pipe)

                else:
                    move_to_position(value2, sign_value, abs_value, DAQdll, pipe)

                # 调整后再检查X、Y轴的运动并更新current_x和current_y
                current_x, current_y = adjust_xy_position_after_movement(current_x, current_y, x_target, y_target, pipe)

                if value2 == 536:
                    adjust_fai_position_after_movement(fai_target, current_fai, pipe)

                

                if value1 < 460 < value2 and valve_status == 'open':
                    robot.valveclose()
                    valve_status = 'closed'
                    pipe.send(('UPDATE_VALVE_STATUS', 'closed'))
                    print("阀门已关闭")

                pipe.send(('UPDATE_VALUE1_POSITION', value2))

        time.sleep(0.1)

def move_to_position(target_position, sign_value, abs_value, DAQdll, pipe):
    abs_value = int(abs_value * 12500)
    erro = DAQdll.openUSB()
    if erro != 0:
        print("设备打开失败")
        return

    DAQdll.Set_Axs(0, 0, 0)
    DAQdll.Set_Axs(0, 0, 1)
    DAQdll.DeltMov(0, 0, 0, int(sign_value), 0, 1000, 40000, abs_value, 0, 100, 100)

    Pos = c_uint(1)
    RunState = c_char(1)
    IOState = c_char(1)
    CEMG = c_char(1)

    while True:
        if pipe.poll():
            stop_signal = pipe.recv()
            if stop_signal == "STOP":
                DAQdll.AxsStop(0, 0, 0)
                print("急停信号收到，传动轴已停止运动")
                return

        erro = DAQdll.Read_Position(0, 0, byref(Pos), byref(RunState), byref(IOState), byref(CEMG))

        if RunState.value == b'\x00':
            print(f"到达目标位置: {target_position}")
            break

        time.sleep(0.1)

    DAQdll.closeUSB()

def adjust_xy_position_after_movement(current_x, current_y, target_x, target_y, pipe):
    """调整 X/Y 轴到目标位置"""
    if current_x != target_x:
        current_x = adjust_x_position(target_x, pipe, current_x)  # 更新 current_x
    if current_y != target_y:
        current_y = adjust_y_position(target_y, pipe, current_y)  # 更新 current_y

    # 返回最新的current_x 和 current_y
    return current_x, current_y


def adjust_x_position(target_x, pipe, current_x):
    """调整 X 轴到指定目标位置"""
    if current_x != target_x:
        robot.Xposition_move_in()

        while current_x != target_x:
            if current_x < target_x:
                robot.Xposition_target_01mm()
                current_x += 1
            elif current_x > target_x:
                robot.Xposition_target_10mm()
                current_x -= 1
            pipe.send(('UPDATE_X_POSITION', current_x))

        robot.Xposition_move_out()

    # 返回调整后的current_x
    return current_x

def adjust_y_position(target_y, pipe, current_y):
    """调整 Y 轴到指定目标位置"""
    if target_y != current_y:
        robot.Yposition_move_in()

        while current_y != target_y:
            if current_y < target_y:
                robot.Yposition_target_01mm()
                current_y += 1
            elif current_y > target_y:
                robot.Yposition_target_10mm()
                current_y -= 1
            pipe.send(('UPDATE_Y_POSITION', current_y))

        robot.Yposition_move_out()

    # 返回调整后的current_y
    return current_y


def adjust_fai_position(target_fai, current_fai, pipe):
    """调整 FAI 轴到指定目标位置，不依赖点击"""
    if target_fai != current_fai :
        print(f"调整 FAI 轴到目标位置: {target_fai}")
        robot.fai_get_in()

        while current_fai != target_fai:
            if current_fai < target_fai:
                robot.fai_5move135()
                current_fai += 130
            elif current_fai > target_fai:
                robot.fai_135move5()
                current_fai -= 130

            pipe.send(('UPDATE_FAI_POSITION', current_fai))

        robot.fai_get_out()

    # 返回最新的current_x 和 current_y
    return current_fai

def adjust_fai_position_after_movement(target_fai, current_fai, pipe):
    """运动后调整 FAI 轴"""
    if current_fai != target_fai:
        adjust_fai_position(target_fai, current_fai, pipe)

def main():
    parent_conn, child_conn = multiprocessing.Pipe()
    app_process = multiprocessing.Process(target=position.run_app, args=(parent_conn,))
    app_process.start()
    process_movement(child_conn)
    app_process.join()

if __name__ == "__main__":
    main()
