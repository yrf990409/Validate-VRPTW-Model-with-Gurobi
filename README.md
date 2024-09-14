
# Gurobi (Python) 求解VRPTW
NOTICE：本md文档使用Typora编写，使用其他编辑器可能导致公式显示不正确。

##  背景

在接触车辆路径优化时，第一次听说Gurobi求解器。学习使用Gurobi并正确地建模求解经典VRPTW问题并不是一个简单的事情。有关Gurobi学习的相关资料并没有遍地开花，因此简单写个代码，使用Python调用Gurobi求解VRPTW问题。

代码尽可能简单，因为我也是初学者，如果有能对你有帮助，将是我的荣幸。如果有错误，希望我们一起认真讨论。

**注意：此代码仅验证了该模型的准确性，并不能作为一个有效求解的方法！**

## 安装 & 使用

在运行这个代码之前，你需要如下配置好并能使用的软件：

- python 3.x
- Gurobi 9.x

同样，除此之外，你还需要Solomon数据集，所罗门数据集需要处理成csv文件(去除BOM信息，UTF-8格式)，放在Data文件夹下。有关Solomon数据集相关的问题及下载，请参考[这里](https://www.sintef.no/projectweb/top/vrptw/100-customers/)。

将csv文件在代码中设置。

```python
data = np.loadtxt('./Data/c101.csv',  # 相对路径下的csv文件，可替换成你的数据
                  dtype=None,         # 数据类型默认
                  encoding='UTF-8',   # 注意此文件为UTF-8格式且取消BOM
                  delimiter=',')      # 分隔符
```

设置车辆可使用数和容积。

```python
# 车辆数据
# 车辆数据的大小请查阅Solomon原始txt文件中的定义
v_cap = 200
v_num = 25
```

## 解决的数学模型

经典VRPTW问题的模型构建，请参考[Jean-François Cordeau (2002)](https://doi.org/10.1137/1.9780898718515.ch7);

同时，还参考了微信公众号运小筹的[此篇文章](https://mp.weixin.qq.com/s/tF-ayzjpZfuZvelvItuecw)。


## 结果输出

Gurobi将输出模型(.lp)，结果(.sol)，日志(.log)三个文件，代码将对求解结果进行绘制、保存路线图，打印路线方案。

## 后续完善
将继续基于此代码复现高引论文中的算法。

## 致谢

作者感谢下列组织和个人对这个简单代码的支持：

- 运小筹（微信公众号）
- Gurobi（中国代理）



