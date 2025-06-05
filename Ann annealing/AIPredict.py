import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from joblib import load

# 在程序启动时加载归一化器
scaler_values = load('scaler_values.joblib')
scaler_outputs = load('scaler_outputs.joblib')

# 加载模型
model = load_model('model.h5')

class AI_Controller:
    def __init__(self, setpoint, output_limits=(0, 3.85), log_function=None, max_change_rate=0.05, heating_rate=1.0):
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.log_function = log_function
        self.max_change_rate = max_change_rate  # 最大变化率
        self.heating_rate = heating_rate  # 使用传递的加热速率

    def ai_predict(self, current_value):
        """
        作成的未来温度信息进行AI预测。

        参数:
        - current_value: 当前电流值 (float)

        返回:
        - 预测的电流值 (float)
        """
        try:
            ### 1. 构建未来温度矩阵 (20维) ###
            # 初始化未来温度矩阵
            future_temperature = np.zeros((1, 20))
            future_temperature[0, 0] = current_value

            # 根据 current_value 和 self.setpoint 计算梯度并填充未来温度矩阵
            for i in range(1, 20):

                # 计算当前值与 setpoint 的距离
                distance_to_setpoint = abs(current_value - self.setpoint)

                # 根据距离调整梯度
                if distance_to_setpoint > 5 + self.setpoint / 20 * self.heating_rate ** 1.5:
                    
                    gradient = self.heating_rate if current_value < self.setpoint else -self.heating_rate / 2
                else:
                    gradient = self.heating_rate / 2

                # 计算下一个值
                next_value = future_temperature[0, i-1] + gradient
                if (gradient > 0 and next_value > self.setpoint) or (gradient < 0 and next_value < self.setpoint):
                    future_temperature[0, i] = self.setpoint
                else:
                    future_temperature[0, i] = next_value

            # 对未来温度矩阵进行归一化
            future_values_scaled = scaler_values.transform(future_temperature)

            ### 2. 使用模型进行预测 ###
            prediction_scaled = model.predict(future_values_scaled, verbose=0)

            ### 3. 反归一化预测结果 ###
            prediction = scaler_outputs.inverse_transform(prediction_scaled)

            ### 4. 将预测值限制为三位小数 ###
            prediction = np.round(prediction, 3)

            return prediction[0, 0]

        except Exception as e:
            print(f"AI Prediction failed: {e}")
            # 在预测失败时，返回当前电流值
            return current_value
