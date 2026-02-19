import numpy as np

def calculate_gaia_distance(plx):
    return 1000.0 / plx if plx and plx > 0 else None

def calculate_cepheid_distance(P, V, I, J, K):
    # 1. Инфракрасный (самый точный)
    if not np.isnan(J) and not np.isnan(K):
        W = K - 0.69 * (J - K)
        M_W = -3.284 * (np.log10(P) - 1.0) - 5.588
        return 10**((W - M_W + 5)/5), "Cepheid(IR)"
    # 2. Оптический
    if not np.isnan(V) and not np.isnan(I):
        W = I - 1.55 * (V - I)
        M_W = -3.31 * (np.log10(P) - 1.0) - 5.80
        return 10**((W - M_W + 5)/5), "Cepheid(Opt)"
    return None, None

def calculate_rr_lyrae_distance(P, V, K):
    if not np.isnan(K):
        M_k = -2.33 * np.log10(P) - 0.93
        return 10**((K - M_k + 5)/5), "RR_Lyrae(K)"
    if not np.isnan(V):
        return 10**((V - 0.6 + 5 - 0.5)/5), "RR_Lyrae(V)"
    return None, None