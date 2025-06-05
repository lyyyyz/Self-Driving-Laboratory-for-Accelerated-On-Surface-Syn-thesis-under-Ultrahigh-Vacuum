'''
机器训练模型
'''
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from data import process_data  # 导入 process_data 函数
from joblib import dump, load

def create_model(input_dim):
    model = Sequential([
        Input(shape=(input_dim,)),  # 使用 Input 层定义输入形状
        Dense(64, activation='swish'),  # 增加神经元数量并使用 swish 激活函数
        Dense(32, activation='relu'),
        Dense(16, activation='relu'),
        Dense(1, activation='linear')
    ])
    # 使用均方误差作为损失函数
    model.compile(optimizer=Adam(learning_rate=0.00005), loss='mean_squared_error')  # 调整学习率
    return model

def cross_validate_model(future_values_matrix_array, outputs_matrix_array, n_splits=5):
    # 对 future_values_matrix_array 进行归一化
    scaler_values = MinMaxScaler()
    future_values_scaled = scaler_values.fit_transform(future_values_matrix_array)
    dump(scaler_values, 'scaler_values.joblib')  # 保存归一化器

    # 对 outputs_matrix_array 进行归一化
    scaler_outputs = MinMaxScaler()
    outputs_scaled = scaler_outputs.fit_transform(outputs_matrix_array)
    dump(scaler_outputs, 'scaler_outputs.joblib')  # 保存归一化器

    # 初始化 KFold
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    mse_scores = []

    for train_index, test_index in kf.split(future_values_scaled):
        X_train, X_test = future_values_scaled[train_index], future_values_scaled[test_index]
        y_train, y_test = outputs_scaled[train_index], outputs_scaled[test_index]

        # 创建和训练模型
        model = create_model(X_train.shape[1])
        model.fit(X_train, y_train, epochs=200, batch_size=64, verbose=0)

        # 预测和评估
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        mse_scores.append(mse)

    # 保存模型
    model.save('model.h5')

    print(f"Cross-validated MSE scores: {mse_scores}")
    print(f"Average MSE: {np.mean(mse_scores)}")

if __name__ == "__main__":
    # 从 data.py 中获取 future_values_matrix_array 和 outputs_matrix_array
    file_path = 'new_experiment_log.txt'
    output_file_path = 'matrix_output.txt'
    outputs_matrix_array, future_values_matrix_array = process_data(file_path)

    # 进行交叉验证
    cross_validate_model(future_values_matrix_array, outputs_matrix_array)
