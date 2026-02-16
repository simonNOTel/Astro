import numpy as np


def calculate_gaia_distance(parallax_mas):
    """Переводит параллакс (mas) в расстояние (парсеки)."""
    if parallax_mas is None or parallax_mas <= 0 or np.isnan(parallax_mas):
        return None
    return 1000 / parallax_mas


def calculate_wesenheit_distance(period, v_mag, i_mag):
    """
    МЕТОД 1 (ТОЧНЫЙ): Индекс Везенайта.
    Игнорирует пыль, но требует фильтров V и I.
    """
    if v_mag is None or i_mag is None:
        return None

    # Наблюдаемый индекс
    W_obs = i_mag - 1.55 * (v_mag - i_mag)

    # Абсолютный индекс (калибровка Fouque et al. 2007)
    log_P = np.log10(period)
    M_W = -3.31 * (log_P - 1.0) - 5.80

    # Расстояние
    distance_pc = 10 ** ((W_obs - M_W + 5) / 5)
    return distance_pc


def calculate_basic_distance(period, v_mag):
    """
    МЕТОД 2 (ЗАПАСНОЙ): Классический закон Ливитта.
    Используется, если нет данных I. Принимаем среднее поглощение Av ~ 0.5 mag.
    """
    if v_mag is None:
        return None

    # Абсолютная величина Mv (калибровка Feast & Catchpole 1997)
    M_v = -2.81 * np.log10(period) - 1.43

    # Среднее поглощение (заглушка, так как мы не знаем точного)
    Av_estimate = 0.5

    # Модуль дистанции: m - M = 5 log d - 5 + Av
    # 5 log d = m - M + 5 - Av
    distance_pc = 10 ** ((v_mag - M_v + 5 - Av_estimate) / 5)
    return distance_pc