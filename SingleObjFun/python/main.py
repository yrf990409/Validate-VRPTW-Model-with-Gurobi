# coding=utf8
'''
Python 调用gurobi求解VRPTW问题
@ Author: Yrf990409
1st. April. 2022
此代码与jupyter代码相同,作为补充用
'''
#%% 导入所需包
import gurobipy as gp
import numpy as np
import math
import copy
import matplotlib.pyplot as plt

#%% 定义Delta索引
def DeltaPlus(i,V): 
    # DeltaPlus 之后访问的点的集合
    delta_plus = copy.deepcopy(V) # 深拷贝，否则对V直接操作
    delta_plus.remove(0) # i之后访问的点不能是出发点
    if i != 0:
        delta_plus.remove(i) # i之后访问的点不能是自身
    return delta_plus

def DeltaMinus(i,V):
    # DeltaMinus 之前访问的点的集合
    delta_minus = copy.deepcopy(V) # 深拷贝，否则对V直接操作
    if i != delta_minus[-1]:
        delta_minus.remove(i) # 到达i的点不能是自身
        del delta_minus[-1]   # 到达i的点不能是返回点
    else:
        del delta_minus[-1]   # 到达i的点不能是返回点或自身
    return delta_minus

#%% 数据处理
# 导入数据
np.set_printoptions(suppress=True)    # 取消numpy打印的科学计数法
data = np.loadtxt('./Data/c101.csv',  # 相对路径下的csv文件，可替换成你的数据
                  dtype=None,         # 数据类型默认
                  encoding='UTF-8',   # 注意此文件为UTF-8格式且取消BOM
                  delimiter=',')      # 分隔符

'''
关于Slomon数据的每列数据的定义,可查看下列代码
也可以访问 https://www.sintef.no/projectweb/top/vrptw/100-customers/
下载原始txt数据
原始数据仅转换成CSV格式,并未增删,因此需要进一步处理
'''
# 数据提取，处理
# 数据切片
x_coord  = np.append(data[:,1],data[0,1])   # 横坐标
y_coord  = np.append(data[:,2],data[0,2])   # 纵坐标
demands  = np.append(data[:,3],data[0,3])   # 需求
ready_t  = np.append(data[:,4],data[0,4])   # 左时间窗
due_t    = np.append(data[:,5],data[0,5])   # 右时间窗
serve_t  = np.append(data[:,6],data[0,6])   # 服务时长

# 车辆数据
# 车辆数据的大小请查阅Solomon原始txt文件中的定义
v_cap = 200 # solomon数据集中 1系列容量为200 2系列容量为1000
v_num = 25

# 定义集合
V = [(i) for i in range(x_coord.size)] 
N = V[1:-1]
A = [(i,j) for i in V for j in V]
K = [(k) for k in range(v_num)]
# print(V) # 0,1,...,101
# print(N) # 1,2,...,100
# print(A) # (0,0)至(101,101)
# print(K) # 0,1,...,24

# 定义时间上下界
E = float(ready_t[0])
L = float(due_t[0])

M = 10000 # 定义大M

C = v_cap # 定义容量

# 距离矩阵计算(字典)
# 欧式距离
c = {(i,j):
    math.sqrt((x_coord[i]-x_coord[j])**2 + 
              (y_coord[i]-y_coord[j])**2)
    for i in V
    for j in V}
# print(len(c)) # 102*102

t = copy.deepcopy(c) # 行驶时间矩阵
a = {(i):ready_t[i] for i in V} # 左时间窗
b = {(i):due_t[i] for i in V}   # 右时间窗
s = {(i):serve_t[i] for i in V} # 服务时长
d = {(i):demands[i] for i in N} # 客户需求

#%% 实例化模型
m = gp.Model()

#%% 创建决策变量
# 决策变量x_ijk
x = m.addVars(((i,j,k) for (i,j) in A for k in K),
                vtype = gp.GRB.BINARY,  # 0-1变量
                name = 'x')             # 名称为‘x’

# 决策变量w_ik
w = m.addVars(((i,k) for i in V for k in K),
                vtype = gp.GRB.CONTINUOUS,
                name = 'w')

#%% 目标函数
# $$
# {\rm{min}}\,\,\ \sum_{k\in K}\sum_{(i,j)\in A}c_{ij}x_{ijk}
# \tag{1}
# $${Latex}
m.setObjective(gp.quicksum(c[i,j]*x[i,j,k]
                            for (i,j) in A
                            for k in K),
                            sense = gp.GRB.MINIMIZE)

#%% 约束
# 一个顾客只能被一辆车服务一次
# $$
# \sum_{k\in K}\,\sum_{j\in \Delta^{+}(i)}x_{ijk} = 1,\,\,\forall i \in N
# \tag{2}
# $$ {Latex}
for i in N:
    l_exp = gp.LinExpr() # 声明一个线性表达式
    for j in DeltaPlus(i, V):
        for k in K:
            l_exp.addTerms(1, x[i,j,k]) # 向表达式添加项
    m.addConstr(l_exp==1,name='VServesC'+str(i))

# 所有车辆必须出发
# $$
# \sum_{j\in \Delta^+(0)}x_{0jk}= 1,\,\, \forall k \in K
# \tag{3}
# $$ {Latex}
for k in K:
    m.addConstr(gp.quicksum(x[0,j,k] 
                            for j in DeltaPlus(0,V))==1,
                name='Outbound'+str(k))

# 流守恒约束
# $$
# \sum_{i\in \Delta^-(j)}x_{ijk} = \sum_{i\in \Delta^+(j)}x_{jik},\,\, \forall k\in K ,\,j\in N
# \tag{4}
# $$ {Latex}
for k in K:
    for j in N:
        m.addConstr(gp.quicksum(x[i,j,k] for i in DeltaMinus(j,V))
                 == gp.quicksum(x[j,i,k] for i in DeltaPlus(j,V)),
                    name = 'Flow'+str(k)+'&'+str(j))

# 所有车辆必须回到配送中心
# $$
# \sum_{i\in \Delta^-(n+1)}x_{i,n+1,k}=1,\,\, \forall k\in K
# \tag{5}
# $$ {Latex}
for k in K:
    m.addConstr(gp.quicksum(x[i,V[-1],k] 
                            for i in DeltaMinus(V[-1],V))==1,
                name='Inbound'+str(k))

# 时间关系推导
# $$
# w_{ik}+s_i+t_{ij}-w_{jk} \le (1-x_{ijk})M,\,\,\forall k\in K,\,(i,j)\in A
# \tag{6a}
# $$ {Latex}
for (i,j) in A:
    for k in K:
        m.addConstr((w[i,k]+s[i]+t[i,j]-w[j,k]
                      <=(1-x[i,j,k])*M),
                    name = 'Time'+str(i)+'&'+str(j)+'&'+str(k))

# 时间窗约束
# $$
# a_i\sum_{j\in \Delta^+(i)}x_{ijk} \le w_{ik} \le b_i\sum_{j\in \Delta^+(i)}x_{ijk} ,\,\, \forall k \in K,\,i\in N
# \tag{7}
# $$ {Latex}
# $$
# E\le w_{ik}\le L,\,\, \forall k \in K ,\, i\in \{0,n+1\}
# \tag{8}
# $$ {Latex}
for k in K:
    for i in N:
        m.addConstr((a[i]*(gp.quicksum(x[i,j,k] for j in DeltaPlus(i,V)))<=w[i,k]),
                    name = 'TimeWindow1'+str(i)+'&'+str(k))

for k in K:
    for i in N:
        m.addConstr((w[i,k]<=b[i]*(gp.quicksum(x[i,j,k] for j in DeltaPlus(i,V)))),
                    name = 'TimeWindow2'+str(i)+'&'+str(k))

for i in [0,V[-1]]:
    for k in K:
        m.addConstr( E<=w[i,k],name='TimeBound1'+str(i)+str(k))

for i in [0,V[-1]]:
    for k in K:
        m.addConstr( w[i,k]<=L,name='TimeBound2'+str(i)+str(k))

# 容量约束
# $$
# \sum_{i\in N}d_i\sum_{j\in \Delta^+(i)}x_{ijk}\le C,\,\, \forall k \in K
# \tag{9}
# $$ {Latex}
for k in K:
    l_exp = gp.LinExpr() # 线性表达
    for i in N:
        for j in DeltaPlus(i,V):
            l_exp.addTerms(d[i],x[i,j,k])
    m.addConstr(l_exp<=C,name='Cap'+str(k))

#%% 求解
m.Params.MIPGap = 0.01
m.Params.timeLimit = 7200
m.Params.LogFile =  "SolvingLog.log"

m.optimize()
m.write('Model.lp')
m.write('Solution.sol')

print('求解完成')

#%% 结果分析
solution  = {}
delimiter = [] # 用于分割车辆

count = 0 # 计数器
for k in K:
    for i in V:
        for j in V:
            if math.isclose(x[i,j,k].X,1): # 得到的解不一定是整数不能用“==”
                solution[i,j,k] = 1
                count = count+1
    delimiter.append(count)

route = np.array(list(solution.keys())) # 储存等于k经过的弧(i,j)

#%% 路径打印 & 画图
plt.figure(dpi=1000)
for i in delimiter:
    if i == delimiter[0]: # route第一辆车
        route_for_k = route[0:i,:] 

        # 如果车没使用，直接从出发到返回
        if route_for_k[0,0] == 0 and route_for_k[0,1] == V[-1]:
            print(f'第{route_for_k[0,-1]}辆车的路径为:{0} -> {V[-1]}')
        else: # 如果使用了
            # 先画个从至表
            table = np.zeros((V[-1]+1,V[-1]+1))
            for k in range(route_for_k.shape[0]):
                table[route_for_k[k,0],route_for_k[k,1]] = 1
            # 从至表里面读取信息
            start = 0
            passing = 0
            end = V[-1]
            print(f'第{route_for_k[0,-1]}辆车的路径为:{0}',end='')
            while passing != end:
                temp = table[start,:]
                passing = int(np.argwhere(temp==1))
                plt.plot((x_coord[start],x_coord[passing]),
                         (y_coord[start],y_coord[passing]),c='blue',linewidth=0.8)
                plt.text(x_coord[passing],
                         y_coord[passing], passing ,ha='center', va='bottom', fontsize=5)
                start = passing
                print(f' -> {passing}',end='')
            else:
                print()
    else:
        route_for_k = route[delimiter[delimiter.index(i)-1]:i]
        # print(route_for_k)
        # 如果车没使用，直接从出发到返回
        if route_for_k[0,0] == 0 and route_for_k[0,1] == V[-1]:
            print(f'第{route_for_k[0,-1]}辆车的路径为:{0} -> {V[-1]}')
        else: # 如果使用了
            # 先画个从至表
            table = np.zeros((V[-1]+1,V[-1]+1))
            for k in range(route_for_k.shape[0]):
                table[route_for_k[k,0],route_for_k[k,1]] = 1
            # 从至表里面读取信息
            start = 0
            passing = 0
            end = V[-1]
            print(f'第{route_for_k[0,-1]}辆车的路径为:{0}',end='')

            while passing != end:
                temp = table[start,:]
                passing = int(np.argwhere(temp==1))
                plt.plot((x_coord[start],x_coord[passing]),
                         (y_coord[start],y_coord[passing]),c='blue',linewidth=0.8)
                plt.text(x_coord[passing],
                         y_coord[passing], passing ,ha='center', va='bottom', fontsize=5) 
                start = passing
                print(f' -> {passing}',end='')
            else:
                print()

plt.savefig('route.png')
plt.show()