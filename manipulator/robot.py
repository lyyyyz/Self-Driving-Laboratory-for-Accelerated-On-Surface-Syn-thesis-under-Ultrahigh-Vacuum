#robot.py
import sys
import time
import os
import jkrc # type: ignore


##机械臂开机##
def power_on ():
    '机械臂开机'
    print('机械臂开机')
    robot = jkrc.RC("10.5.5.100")
    robot.login()
    robot.power_on()
    robot.logout()

##机械臂上使能##
def enable ():
    '机械臂上使能'
    print('机械臂上使能')
    robot = jkrc.RC("10.5.5.100")
    robot.login()
    robot.enable_robot()
    robot.logout()

##机械臂下使能##
def disable ():
    '机械臂下使能'
    print('机械臂下使能')
    robot = jkrc.RC("10.5.5.100")
    robot.login()
    robot.disable_robot()
    robot.logout()

##机械臂关机##
def power_off ():
    print('机械臂关机')
    robot = jkrc.RC("10.5.5.100")
    robot.login()
    robot.power_off()
    robot.logout()



##开阀门##
def valveopen():
    print('开阀门')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("valveopen")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

##关阀门##
def valveclose():
    print('关阀门')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("valveclose")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()


##到X轴预备位置##
def Xposition_move_in():
    print('到X轴预备位置')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Xposition_move_in")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

##退出X轴位置##
def Xposition_move_out():
    print('退出X轴位置')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Xposition_move_out")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()



##X坐标前进1mm##
def Xposition_target_01mm():
    print('X坐标前进1mm')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Xposition_target_01mm")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

    

##X坐标退出1mm##
def Xposition_target_10mm():
    print('X坐标退出1mm')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Xposition_target_10mm")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()




##到Y轴预备位置##
def Yposition_move_in():
    print('到Y轴预备位置')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Yposition_move_in")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

##退出Y轴位置##
def Yposition_move_out():
    print('退出Y轴位置')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Yposition_move_out")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()



##Y坐标前进1mm##
def Yposition_target_01mm():
    print('Y坐标前进1mm')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Yposition_target_01mm")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

    

##Y坐标退出1mm##
def Yposition_target_10mm():
    print('Y坐标退出1mm')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("Yposition_target_10mm")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()


##到fai预备位置##
def fai_get_in():
    print('到fai预备位置')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("fai_get_in")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

##退出fai预备位置##
def fai_get_out():
    print('退出fai预备位置')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("fai_get_out")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()

##fai从5度到135度##
def fai_5move135():
    print('fai从5度到135度')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("fai_5move135")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()


##fai从135度到5度##
def fai_135move5():
    print('fai从135度到5度')

    robot = jkrc.RC("10.5.5.100")

    robot.login()

    ret = robot.program_load("fai_135move5")

    a = (0, 0)

    robot.program_run()

    time.sleep(1)

    while True:
        if a[1] == 1:
            break
        else:
            a = robot.get_digital_output(0, 2)

    robot.logout()