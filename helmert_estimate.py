# Helmert Variance Component Estimation

import numpy as np

# k=2
B1 = np.array([[0.5532, -0.8100, 0, 0],
               [0.2434, 0.5528, 0, 0],
               [-0.7966, 0.2572, 0, 0],
               [-0.2434, -0.5528, 0, 0],
               [0.6298, 0.6368, 0, 0],
               [-0.3864, -0.0840, 0, 0],
               [0.7966, -0.2572, -0.2244, -0.3379],
               [-0.8350, -0.1523, 0.0384, 0.4095],
               [0.0384, 0.4095, 0.1860, -0.0716],
               [-0.0384, -0.4095, 0.2998, 0.1901],
               [-0.3480, 0.3255, -0.0384, -0.4095],
               [0.3864, 0.0840, -0.2614, 0.2194]])

B2 = np.array([[0.3072, 0.9516, 0, 0],
               [-0.9152, 0.4030, 0, 0],
               [0.2124, -0.9722, 0, 0],
               [0, 0, -0.6429, -0.7660],
               [0, 0, -0.8330, 0.5532],
               [0.9956, -0.0934, -0.9956, 0.0934]])
B = np.vstack((B1, B2))

L1 = np.array([0.18, -0.53, 3.15, 0.23, -2.44, 1.01, 2.68, -4.58, 2.80, -3.10, 8.04, -1.14])
L1 = -L1.T
L2 = np.array([-0.84, 1.54, -3.93, 2.15, -12.58, -8.21])
L2 = -L2.T
L = np.hstack((L1, L2))

n_obs1 = 12
n_obs2 = 6

# 初始 P
sita = np.array([1.5 * 1.5, 2.0 * 2.0])

count = 0
while True:
    sita1 = sita[0] / sita[0]
    sita2 = sita[0] / sita[1]
    P1 = np.diag(sita1 * np.ones(n_obs1))
    P2 = np.diag(sita2 * np.ones(n_obs2))
    P = np.diag(np.hstack((sita1 * np.ones(n_obs1), sita2 * np.ones(n_obs2))))

    N1 = np.dot(B1.T, P1).dot(B1)
    N2 = np.dot(B2.T, P2).dot(B2)
    N = np.dot(B.T, P).dot(B)
    W = np.dot(B.T, P).dot(L)

    N_ = np.linalg.inv(N)
    X = np.dot(N_, W)
    V1 = np.dot(B1, X) - L1
    V2 = np.dot(B2, X) - L2

    VV1 = np.dot(V1.T, P1).dot(V1)
    VV2 = np.dot(V2.T, P2).dot(V2)

    # Helmert Matrix
    S = np.array([[n_obs1 - 2 * np.trace(N_ * N1) + np.trace(N_ * N1 * N_ * N1), np.trace(N_ * N1 * N_ * N2)],
                  [np.trace(N_ * N1 * N_ * N2), n_obs2 - 2 * np.trace(N_ * N2) + np.trace(N_ * N2 * N_ * N2)]])
    sita = np.dot(np.linalg.inv(S), np.hstack((VV1, VV2)).T)
    count += 1
    print("helmet进行次数{0}，单位权方差 {1} {2}，比值 {3}".format(count, sita[0], sita[1], sita[0] / sita[1]))
    # loop out
    if abs(max(sita)/min(sita)) - 1 < 0.01:
        break

    # update
    sita[0] = sita[0] / sita1
    sita[1] = sita[1] / sita2
