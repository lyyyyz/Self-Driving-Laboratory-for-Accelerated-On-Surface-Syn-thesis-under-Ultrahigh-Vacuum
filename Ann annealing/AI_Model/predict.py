'''
可以对模型进行基本的测试
'''
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from joblib import load

def predict(current_value, setpoint):
    input_matrix = np.zeros((1, 20))
    input_matrix[0, 0] = current_value

    # 根据 current_value 和 self.setpoint 计算梯度
    for i in range(1, 20):
        # 计算当前值与 setpoint 的距离
        distance_to_setpoint = abs(input_matrix[0, i-1] - setpoint)

        # 根据距离调整梯度
        if distance_to_setpoint > 15:
            gradient = 0.8 if current_value < setpoint else -0.5
        else:
            gradient = 0.2

        # 计算下一个值
        next_value = input_matrix[0, i-1] + gradient
        if (gradient > 0 and next_value > setpoint) or (gradient < 0 and next_value < setpoint):
            input_matrix[0, i] = setpoint
        else:
            input_matrix[0, i] = next_value
    
    print(input_matrix)

    # 对输入矩阵进行归一化
    input_scaled = scaler_values.transform(input_matrix)

    # 使用模型进行预测
    prediction_scaled = model.predict(input_scaled)

    # 反归一化预测结果
    prediction = scaler_outputs.inverse_transform(prediction_scaled)

    # 将预测值限制为三位小数
    prediction = np.round(prediction, 3)  # 对整个预测数组进行四舍五入

    return prediction

if __name__ == "__main__":
    # 在程序启动时加载归一化器
    scaler_values = load('scaler_values.joblib')
    scaler_outputs = load('scaler_outputs.joblib')

    # 加载模型
    model = load_model('model.h5')

    current_value = 302
    setpoint = 302

    prediction = predict(current_value, setpoint)
    print(prediction)

