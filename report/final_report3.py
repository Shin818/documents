# モデル3

import numpy as np
import matplotlib.pyplot as plt
from pandas import read_csv

# module part
# 対数尤度関数の勾配ベクトルとヘシアン
def diff(Beta, c):
    # N:サンプル数, I:選択肢数, K:パラメータ数
    N = len(c.Choice)
    I = max(c.Choice)
    K = len(Beta)
    # 効用関数パラメータ
    ASC_Car, ASC_Bus, B_TIME, B_FARE, B_AgeC = Beta
    # 選択結果判定指標
    Choice = np.array([(c.Choice == 1), (c.Choice == 2), (c.Choice == 3)])
    # 効用関数
    V = np.array([
        ASC_Car + B_TIME * c.TimeC + B_FARE * c.FareC + B_AgeC * c.Age,
        ASC_Bus + B_TIME * c.TimeB + B_FARE * c.FareB,
        B_TIME * c.TimeR + B_FARE * c.FareR
    ])
    # ロジットモデルの選択確率と尤度
    PD = (np.array([c.AvailC, c.AvailB, c.AvailR]) * np.exp(V)).sum(axis=0)
    P = np.array([c.AvailC, c.AvailB, c.AvailR]) * np.exp(V) / PD
    ind_L = np.log(sum(Choice * P))
    f = -ind_L.sum()

    # 選択肢の特性値をまとめた行列 #####効用関数と整合的にする
    X = np.array([
        [np.ones(N),  np.zeros(N), c.TimeC, c.FareC, c.Age],
        [np.zeros(N),  np.ones(N), c.TimeB, c.FareB, np.zeros(N)],
        [np.zeros(N), np.zeros(N), c.TimeR, c.FareR, np.zeros(N)]
    ])

    # 対数尤度関数のヤコビアン
    grad_f = np.empty([K, I, N])
    for k in range(K):
        grad_f[k, :, :] = (Choice-P) * X[:, k]
    grad_f = np.sum(np.sum(grad_f, axis=1), axis=1)

    # 対数尤度関数のヘシアン
    # hoge:計算を簡易にするための行列
    hoge = np.empty([K, I, N])
    for k in range(K):
        hoge[k, :, :] = X[:, k]*P
    hoge = np.sum(hoge, axis=1)
    # ヘシアンの計算
    hess_f = np.empty([K, K, I, N])
    for k_1 in range(K):
        for k_2 in range(K):
            hess_f[k_1, k_2, :, :] = - \
                (P * (X[:, k_1]-hoge[k_1, :]) * (X[:, k_2]-hoge[k_2, :]))
    hess_f = np.sum(np.sum(hess_f, axis=2), axis=2)

    # 定義したdiffが返す値
    return f, grad_f, hess_f


# 多変数のニュートン法
def NR(x_ini, max_iter, tol, data):
    hist = np.empty([max_iter, len(x_ini)])
    x = x_ini
    for iter in range(max_iter):
        hist[iter] = x
        # 目的関数の偏微分，
        hoge, grad_f, hess_f = diff(x, data)
        newpoint = x-np.dot(grad_f, np.linalg.inv(hess_f))
        stepsize = np.linalg.norm(x-newpoint)
        x = newpoint
        if stepsize < tol:
            hist = hist[:iter]
            break
    return x, hist


# main part

# パラメータ推定
# データ読み込み
c = read_csv('data_final_report.csv')

# 初期値
Beta_ini = [0, 0, 0, 0, 0]
# max_iter:最大反復回数
max_iter = 10
# tol: ステップサイズの閾値
tol = 0.0000000001

# NR法によるパラメータ推定
B_est, hist = NR(Beta_ini, max_iter, tol, c)

##################################################
# 各種統計量の計算
# すべて0で，変数の数だけ要素があるベクトル
B_zero = np.zeros_like(B_est)
# 選択肢固有パラメータ(ASC)以外が0のベクトル
B_c = [B_est[0], B_est[1], 0, 0, 0]

# パラメータベクトルがB_zero,B_cの時の尤度
# B_zeroの時
l_zero, hoge, hoge = diff(B_zero, c)
# B_cの時
l_c, hoge, hoge = diff(B_c, c)

# 推定したパラメータのt検定
# 推定されたパラメータにおける尤度・ヤコビアン・ヘシ アンの計算
l_est, grad_est, hess_est = diff(B_est, c)
# パラメータの標準偏差
stdev = np.sqrt(np.diagonal(-np.linalg.inv(hess_est)))
############################################################
############################################################
print('推定されたパラメータは', B_est)
print('推定されたパラメータの標準偏差は', stdev)
print('t値は ', B_est/stdev)
print('サンプルサイズは', len(c.index))
print('kai-sq_0:', -2*(l_zero-l_est))
print('kai-sq_c:', -2*(l_c-l_est))
print('決定係数は', 1 - (l_est / (l_zero)))
print('自由度調整済みの決定係数は', 1 - (l_est + len(B_est)) / (l_zero))
