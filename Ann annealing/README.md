# Temperature Control System Using ANN Neural Network

## Overview

An innovative temperature control system that employs Artificial Neural Networks (ANN) as an alternative to traditional PID control methods. The system acquires real-time temperature data from experimental equipment via infrared temperature sensors, utilizes a trained ANN model for predictive control, and regulates temperature by controlling heating power sources.

## File Structure

### Core Program Files
| File Name               | Description                                  |
|-------------------------|---------------------------------------------|
| `main_ai.py`            | Main control program (system entry point)   |
| `AIPredict.py`          | ANN model prediction module                 |
| `control.py`            | Heating power supply communication & control|
| `temperature.py`        | Infrared temperature sensor interface       |
| `table.py`              | System status display panel                 |
| `log.py`                | Main logging system                         |
| `temperature_logger.py` | Dedicated temperature data logger           |
| `main_autotest.py`      | Automated data collection utility           |
| `model.h5`              | Pre-trained ANN model file                  |
| `scaler_x.joblib`       | Input data normalization file               |
| `scaler_y.joblib`       | Input data normalization file               |

### AI Model Training Module (`AI_Model/`)
| File Name       | Description                              |
|-----------------|-----------------------------------------|
| `data.py`       | Training data processing & preprocessing|
| `model.py`      | ANN model definition & training program |
| `predict.py`    | Model testing & validation tool         |

## Retraining the ANN Model

To retrain the ANN model with new datasets:
1. Execute the training script:
   ```bash
   cd AI_Model
   python model.py
   ```
2. Replace existing files in the main directory with newly generated:
   - `model.h5` (trained ANN model)
   - `scaler_x.joblib` (input normalization parameters)
   - `scaler_y.joblib` (output normalization parameters)

## Device Communication Note

The communication modules (`control.py` for heating power supply and `temperature.py` for IR sensors) are implemented as example interfaces. These may require hardware-specific modifications when deployed in different systems.

## Technical Support

For technical assistance, please contact:  
**Prof. Yang**  
📧 tr_yang@shu.edu.com  

---

# 基于ANN神经网络的温度控制系统

## 概述

一种使用人工神经网络(ANN)替代传统的PID控制的温度控制系统。系统通过红外测温设备实时获取实验装置的温度数据，并利用训练好的ANN模型进行预测，并通过控制加热电源实现温度调节。

## 文件结构说明

### 核心程序文件
| 文件名称                 | 功能描述                                  |
|--------------------------|-----------------------------------------|
| `main_ai.py`             | 主控制程序，启动整个系统                 |
| `AIPredict.py`           | ANN模型预测程序                         |
| `control.py`             | 加热电源通信与控制模块                   |
| `temperature.py`         | 红外测温设备通信接口                     |
| `table.py`               | 系统状态显示面板                         |
| `log.py`                 | 主日志记录系统                           |
| `temperature_logger.py`  | 温度数据专用记录器                       |
| `main_autotest.py`       | 自动数据收集工具                         |
| `model.h5`               | 预训练的ANN模型文件                      |
| `scaler_x.joblib`        | 输入数据归一化文件                       |
| `scaler_y.joblib`        | 输入数据归一化文件                       |

### AI模型训练模块 (`AI_Model/`)
| 文件名称         | 功能描述                              |
|------------------|-------------------------------------|
| `data.py`        | 训练数据处理与预处理                 |
| `model.py`       | ANN模型定义与训练程序               |
| `predict.py`     | 模型测试与验证工具                  |

## 重新训练ANN模型

用 `AI_Model/model.py` 根据数据文件重新训练模型

训练完成后，将生成的模型文件(`model.h5`)和归一化参数文件(`scaler_*.joblib`)移至主目录替换旧文件。

## 与其他设备的通信

control.py和temperature.py只是示例的通信程序，不适配其他系统

## 技术支持

如遇任何技术问题，请联系：
- tr_yang@shu.edu.com