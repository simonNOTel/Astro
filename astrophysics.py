import numpy as np


def calculate_gaia_distance(parallax_mas):
    if parallax_mas is None or parallax_mas <= 0 or np.isnan(parallax_mas):
        return None
    return 1000 / parallax_mas


# --- ЦЕФЕИДЫ (P > 1 day) ---
def calculate_cepheid_distance(period, v_mag, i_mag, j_mag, k_mag):
    # Пытаемся использовать ИК (JK), если нет - Оптику (VI)

    # 1. Infrared Wesenheit (JK) - Самый точный для пыли
    if j_mag is not None and k_mag is not None:
        W_obs = k_mag - 0.69 * (j_mag - k_mag)
        M_W = -3.284 * (np.log10(period) - 1.0) - 5.588
        return 10 ** ((W_obs - M_W + 5) / 5), "Cepheid(IR)"

    # 2. Optical Wesenheit (VI)
    if v_mag is not None and i_mag is not None:
        W_obs = i_mag - 1.55 * (v_mag - i_mag)
        M_W = -3.31 * (np.log10(period) - 1.0) - 5.80
        return 10 ** ((W_obs - M_W + 5) / 5), "Cepheid(Opt)"

    return None, None


# --- RR ЛИРЫ (P < 1 day) ---
def calculate_rr_lyrae_distance(period, v_mag, k_mag):
    """
    Расчет для звезд RR Лиры.
    Используем K-band (Infrared), так как там зависимость самая четкая.
    """
    if k_mag is None:
        # Если нет ИК, для RR Lyrae Mv примерно константа ~0.6 (грубая оценка)
        if v_mag is not None:
            M_v = 0.6
            # Предполагаем среднее поглощение (тут будет большая погрешность без пыли)
            return 10 ** ((v_mag - M_v + 5 - 0.5) / 5), "RR_Lyrae(V)"
        return None, None

    # Точная формула Muraveva et al. (2018) для K-band
    # Mk = -2.33 * log(P) - 0.93
    M_k = -2.33 * np.log10(period) - 0.93

    # Считаем модуль расстояния (пренебрегая поглощением в K, оно там мизерное)
    distance = 10 ** ((k_mag - M_k + 5) / 5)
    return distance, "RR_Lyrae(K)"