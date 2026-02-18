import numpy as np
import warnings


def process_lightcurve(lc):
    """
    Очищает кривую блеска от нанов, выбросов и нормализует её.
    """
    # Удаляем пустые значения
    lc = lc.remove_nans()

    # Нормализуем и удаляем выбросы (космические лучи)
    lc = lc.normalize().remove_outliers(sigma=5)
    return lc


def find_period(lc, min_period=0.5, max_period=500):
    """
    Находит период пульсации методом Ломба-Скаргла.
    """
    # Строим периодограмму
    pg = lc.to_periodogram(method='lombscargle',
                           minimum_period=min_period,
                           maximum_period=max_period)

    # Находим период в точке максимальной мощности
    period_days = pg.period_at_max_power.value
    max_power = pg.max_power.value

    return period_days, pg, max_power
