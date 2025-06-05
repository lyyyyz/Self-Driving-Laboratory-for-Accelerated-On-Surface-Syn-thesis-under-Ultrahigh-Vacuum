import numpy as np
import pandas as pd
# 定义设计变量,e.g., X1,X2,X3,X4,X5
# 定义各个变量的取值

X1 = np.arange(40, 730, 10) # X1 是连续变量，取值从1.5-5.5， 间隔为0.1 ， i.e., 1.5,1.6,1.7,...,5.5
X2 = np.arange(0, 2400, 10) # X2 是连续变量，取值从1.5-5.5， 间隔为0.1 ， i.e., 1.5,1.6,1.7,...,5.5
X3 = np.arange(300, 400, 5) # X3 是连续变量，取值从0.1-0.7， 间隔为0.1 ， i.e., 0.1, 0.2,....,0.7
#X4 = np.array([1,2,3]) # X4 是分类变量，3类，取值为 1,2,3



# 生成整个定义空间
_X1,_X2,_X3 = np.meshgrid(X1,X2,X3)
Visual_samples = np.vstack([_X1.ravel(), _X2.ravel(),_X3.ravel(),]).T
Visual_samples = pd.DataFrame(Visual_samples)
Visual_samples.columns=['feature_name1','feature_name2','feature_name3']

# 显示前五行，说明生成成功
print(Visual_samples.head(5))

# 保存到本地，命名为 Visual_samples.csv 后续在Bgolearn 中调用
Visual_samples.to_csv('Visual_samples_test02.csv',index=0)