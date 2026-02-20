import numpy as np

def process_lightcurve(lc):
    return lc.remove_nans().normalize().remove_outliers(sigma=5)

def find_period(lc):
    pg = lc.to_periodogram(method='lombscargle', minimum_period=0.1, maximum_period=50)
    return pg.period_at_max_power.value, pg, pg.max_power.value