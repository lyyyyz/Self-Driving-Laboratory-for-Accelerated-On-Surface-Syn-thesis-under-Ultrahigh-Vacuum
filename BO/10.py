import pandas as pd
import Bgolearn.BGOsampling as BGOS

original_file_path = r"C:\Users\Huang Qi\Desktop\AL&自动化\code\existing_experiment_data1025.csv"  # 原始文件路径
data = pd.read_csv(original_file_path)
vs = pd.read_csv('Visual_samples_test1102.csv')

x = data.iloc[:, :-1]  # 读取特征
y = data.iloc[:, -1]  # 读取目标

# 创建 Bgolearn 实例
Bgolearn = BGOS.Bgolearn()

Mymodel = Bgolearn.fit(data_matrix = x, Measured_response = y, virtual_samples = vs, min_search=False)
Mymodel.EI() # 通过UCB 函数从虚拟空间选择点