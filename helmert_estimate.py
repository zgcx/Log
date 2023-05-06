# Helmert Variance Component Estimation

import numpy as np

# 数据采用《抗差最小二乘》
# k=2

A1 = np.array([
    [1.0, 2.0, 4.0],
    [3.6, 1.0, 2.1],
    [2.4, 1.5, 3.0],
    [1.0, 2.0, 3.9],
    [3.5, 1.0, 2.0],
    [-1.0, 3.0, 6.0],
    [5.0, 0.5, 1.1]
])

A2 = np.array([
    [1.0, 2.0, 4.1],
    [4.0, 1.0, 1.9],
    [3.0, 1.0, 2.0]
])

A = np.concatenate((A1, A2), axis=0)

L1 = np.array([
    63.8,
    63.1,
    64.8,
    64.3,
    61.7,
    70.5,
    64.0
]).T

# L2 = np.array([
#     65.0,
#     65.9,
#     56.3
# ]).T

# 粗差
L2 = np.array([
    68.0,
    63.9,
    59.3
]).T

L = np.concatenate((L1, L2), axis=0)

n_obs1 = 7
n_obs2 = 3
k = 0.003

# 初始 P
sita = np.array([1.5 * 1.5, 2.0 * 2.0])

count = 0
while True:
    sita0 = sita[0]
    sita1 = sita0 / sita[0]
    sita2 = sita0 / sita[1]
    P1 = np.diag(sita1 * np.ones(n_obs1))
    P2 = np.diag(sita2 * np.ones(n_obs2))
    P = np.diag(np.hstack((sita1 * np.ones(n_obs1), sita2 * np.ones(n_obs2))))

    N1 = np.dot(A1.T, P1).dot(A1)
    N2 = np.dot(A2.T, P2).dot(A2)
    N = np.dot(A.T, P).dot(A)
    W = np.dot(A.T, P).dot(L)

    # 病态
    N_ = np.linalg.inv(N + k * np.eye(N.shape[0]))
    X = np.dot(N_, W)
    V1 = np.dot(A1, X) - L1
    V2 = np.dot(A2, X) - L2

    VV1 = np.dot(V1.T, P1).dot(V1)
    VV2 = np.dot(V2.T, P2).dot(V2)

    # Helmert Matrix
    S = np.array([[n_obs1 - 2 * np.trace(N_ * N1) + np.trace(N_ * N1 * N_ * N1), np.trace(N_ * N1 * N_ * N2)],
                  [np.trace(N_ * N1 * N_ * N2), n_obs2 - 2 * np.trace(N_ * N2) + np.trace(N_ * N2 * N_ * N2)]])
    sita = np.dot(np.linalg.inv(S), np.hstack((VV1, VV2)).T)
    count += 1
    print("第 {0} 次迭代：".format(count))
    print("真值 X = [10.0,15.0,6.0] 估计值：{0} {1} {2} ".format(X[0], X[1], X[2]))
    print("helmet进行次数{0}，单位权方差 {1} {2}，比值 {3}".format(count, sita[0], sita[1], sita[0] / sita[1]))
    # loop out
    if abs(sita[1] / sita[0]) < 1.01:
        break

    # update
    sita[0] = sita[0] / sita1
    sita[1] = sita[1] / sita2
