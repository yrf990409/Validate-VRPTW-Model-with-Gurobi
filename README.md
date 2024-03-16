
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

经典VRPTW问题的模型构建，
请参考[Jean-François Cordeau (2002)](https://doi.org/10.1137/1.9780898718515.ch7);

同时，还参考了微信公众号运小筹的[此篇文章](https://mp.weixin.qq.com/s/tF-ayzjpZfuZvelvItuecw)。

### 模型符号

VRP问题基于一个完全有向图 $G=(V,A)$，其中 $V$是点的集合， $A$是图中弧的集合，仓库用两个点 $0$（出发点）和 $n+1$（返回点）表示。 $V$中任一点 $\forall i\in V$都有与之对应的时间窗 $[a_i,b_i]$，需求 $d_i$，服务时长 $s_i$。 $A$中每段弧 $(i,j)$都有与之对应的成本 $c_{ij}$和车辆行驶过这段弧的行驶时间 $t_{ij}$。弧 $(0,n+1)$的成本为 $0$，行驶时间为 $0$，即 $c_{0,n+1}=t_{0,n+1}=0$。车辆集合为 $K$，每辆车的容量相同为 $C$。

此外，仓库的时间窗 $[a_0,b_0]=[a_{n+1},b_{n+1}]=[E,L]$是问题中时间的上下界，仓库的需求量为 $0$，仓库的服务时长为 $0$，即 $d_0 = d_{n+1}=s_0=s_{n+1}=0$。

[Jean-François Cordeau (2002)](https://doi.org/10.1137/1.9780898718515.ch7) 提出了一些消减不可行弧即保证可行性的方法，
参见其文章的7.2节。
相同的方法在[Schneider(2016)](https://doi.org/10.1016/j.ejor.2015.09.015
        
        
        
        )也被采用。如感兴趣可参考上述两篇文章中的不可行弧判断方法，这里不详细赘述。

模型的决策变量如下：

-  $x_{ijk},\quad \forall (i,j)\in A,k\in K$为0-1决策变量，即车辆 $k\in K$经过弧 $(i,j)\in A$，取值则为1，否则为0。
-  $w_{ik},\quad \forall i\in V,k\in K$表示车辆 $k\in K$开始服务顾客 $i\in V$的时间点。

### 目标函数

$$
\min \sum_{k\in K}\sum_{(i,j)\in A}c_{ij}x_{ijk}
\tag{1}
$$

### 约束

在定义约束前，着重强调VRPTW问题基于完全有向图，因此定义两个集合 $\Delta^{+}(i)$表示从 $i$出发能到达的点集，即满足 $(i,j)\in A$的 $j$的集合，同理定义 $\Delta^{-}(i)$，表示能到达 $i$的点的集合，即满足 $(j,i)\in A$的 $j$的集合。

定义 $N = V \backslash \{0，n+1 
\}$为客户点的集合。

#### 一个顾客只能被一辆车服务一次

$$
\sum_{k\in K}\sum_{j\in \Delta^{+}(i)}x_{ijk} = 1,\quad\forall i \in N
\tag{2}
$$

理解：对于任何一个在客户集合 $N$中的客户 $i$来说，从 $i$出发到其他在 $\Delta^+(i)$中的车的数量只能有一个。

#### 所有车辆必须出发

$$
\sum_{j\in \Delta^+(0)}x_{0jk}= 1,\quad \forall k \in K
\tag{3}
$$

理解：对于某辆车来说，必须从 $0$出发前往 $ \Delta^+(0)$中的任意一点，这表示车辆可以直接从 $0$前往某个客户，也可以直接前往 $n+1$即仓库，等价于未出发。

#### 流守恒约束

$$
\sum_{i\in \Delta^-(j)}x_{ijk} = \sum_{i\in \Delta^+(j)}x_{jik},\quad \forall k\in K ,j\in N
\tag{4}
$$

理解：对于在 $N$中的任一个客户 $j$来说，每辆车 $k$若从 $\Delta^-(j)$ 中任意一点到达 $j$，那么一定会离开 $j$到达 $\Delta^+(j)$中任意一点。若车辆 $k$从未到达过 $j$，那么 $k$也不可能从 $j$离开。

#### 所有车辆必须回到配送中心

$$
\sum_{i\in \Delta^-(n+1)}x_{i,n+1,k}=1,\quad \forall k\in K
\tag{5}
$$

理解：任一车辆 $k$必须从 $\Delta^-(n+1)$中的任意一点，返回仓库 $n+1$。

#### 时间关系推导

$$
x_{ijk}(w_{ik}+s_i+t_{ij}-w_{jk}) \le 0,\quad\forall k\in K,(i,j)\in A
\tag{6}
$$

理解：对于某辆车 $k\in K$来说，如果访问了弧 $(i,j)$，那么在 $i$开始服务的时间点+在 $i$服务的时长+ $i$到 $j$的时长一定小于等于在 $j$开始服务的时间点，即产生早到会等待。

#### 时间窗约束

$$
a_i\sum_{j\in \Delta^+(i)}x_{ijk} \le w_{ik} \le b_i\sum_{j\in \Delta^+(i)}x_{ijk} ,\quad \forall k \in K,i\in N
\tag{7}
$$

理解：若车辆 $k$不服务节点 $i$，则 $k$在 $i$开始服务的时间点为 $0$。若 $k$服务 $i$，则应该在时间窗范围内服务。

$$
E\le w_{ik}\le L,\quad \forall k \in K , i\in \{0,n+1
\}
\tag{8}
$$

理解：问题的时间上下界，每辆车 $k\in K$出发和回到仓库的时间应在仓库的营业范围之内。

#### 容量约束

$$
\sum_{i\in N}d_i\sum_{j\in \Delta^+(i)}x_{ijk}\le C,\quad \forall k \in K
\tag{9}
$$

理解：对于任一辆车 $k\in K$访问的所有客户（从这个客户出发，即视为服务过这个客户）的总需求小于车辆的容积。

#### 0-1变量约束

$$
x_{ijk} \in \{0,1
\},\quad \forall k\in K,(i,j)\in A
\tag{10}
$$

### 线性化

注意到，公式6为非线性。由于 $x_{ijk}$是0-1变量，因此可以进行下面的转换：

$$
w_{ik}+s_i+t_{ij}-w_{jk} \le (1-x_{ijk})M,\quad\forall k\in K,(i,j)\in A
\tag{6a}
$$

其中， $M$为一个很大的正数。

[Jean-François Cordeau (2002)](https://doi.org/10.1137/1.9780898718515.ch7)指出， $M$实际上是一个与 $(i,j)$相关的数，记为 $M_{ij}$，有 $M_{ij} = {\rm{max}} \{ b_i+s_i+t_{ij}-a_j,0 
\} $。在这里为了简化，直接使用了 $M$。

## 结果输出

Gurobi将输出模型(.lp)，结果(.sol)，日志(.log)三个文件，代码将对求解结果进行绘制、保存路线图，打印路线方案。

## 后续完善
将继续基于此代码复现高引论文中的算法。

## 致谢

作者感谢下列组织和个人对这个简单代码的支持：

- 运小筹（微信公众号）
- Gurobi（中国代理）



