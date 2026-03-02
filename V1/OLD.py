import matplotlib

matplotlib.use('Agg')

import lightkurve as lk
import numpy as np
import matplotlib.pyplot as plt
import warnings
from astroquery.simbad import Simbad

warnings.filterwarnings("ignore", category=UserWarning, module="lightkurve")
warnings.filterwarnings("ignore", category=RuntimeWarning)


def analyze_cepheid(star_name):
    try:
        search_result = lk.search_lightcurve(star_name)
        if len(search_result) == 0:
            return None

        best_index = 0
        for i, mission in enumerate(search_result.mission):
            if 'Kepler' in str(mission):
                best_index = i
                break

        lc = search_result[best_index].download()
        lc = lc.remove_nans().remove_outliers(sigma=5).normalize()

        pg = lc.to_periodogram(method='lombscargle', minimum_period=0.5, maximum_period=100)
        period_days = pg.period_at_max_power.value

        return period_days
    except:
        return None


# --- СПИСОК 50 ЗВЕЗД С НАИМЕНЬШЕЙ ПОГРЕШНОСТЬЮ ---
# Отобраны яркие цефеиды с известными параметрами блеска (V-band)
stars_to_check = [
    {"name": "RT Aur", "m": 5.45}, {"name": "Zeta Gem", "m": 3.91}, {"name": "Eta Aql", "m": 3.90},
    {"name": "X Cyg", "m": 6.39}, {"name": "W Sgr", "m": 4.67}, {"name": "FF Aql", "m": 5.37},
    {"name": "T Vul", "m": 5.75}, {"name": "S Sge", "m": 5.62}, {"name": "X Sgr", "m": 4.54},
    {"name": "Y Sgr", "m": 5.76}, {"name": "V Cen", "m": 6.81}, {"name": "DT Cyg", "m": 5.77},
    {"name": "AX Cir", "m": 5.87}, {"name": "SU Cyg", "m": 6.86}, {"name": "Y Oph", "m": 6.17},
    {"name": "BB Sgr", "m": 6.88}, {"name": "U Sgr", "m": 6.71}, {"name": "SZ Tau", "m": 6.54},
    {"name": "X Lac", "m": 8.42}, {"name": "V473 Lyr", "m": 6.18}, {"name": "U Aql", "m": 6.45},
    {"name": "S Tra", "m": 6.41}, {"name": "R Tra", "m": 6.66}, {"name": "AP Sgr", "m": 6.96},
    {"name": "V350 Sgr", "m": 7.43}, {"name": "V482 Sco", "m": 7.96}, {"name": "Y Car", "m": 7.96},
    {"name": "U Car", "m": 6.29}, {"name": "S CMa", "m": 5.71}, {"name": "T Ant", "m": 9.27},
    {"name": "AW Per", "m": 7.53}, {"name": "V381 Cen", "m": 7.64}, {"name": "MY Pup", "m": 5.68},
    {"name": "SV Vul", "m": 7.24}, {"name": "S Vul", "m": 8.98}, {"name": "CD Cas", "m": 10.8},
    {"name": "RS Cas", "m": 9.98}, {"name": "RY Cas", "m": 9.85}, {"name": "V440 Per", "m": 6.28},
    {"name": "RU Sct", "m": 9.45}, {"name": "U Vul", "m": 7.15}, {"name": "X Pup", "m": 8.46},
    {"name": "AQ Pup", "m": 8.67}, {"name": "SV Mon", "m": 8.24}, {"name": "RX Aur", "m": 7.58},
    {"name": "SY Aur", "m": 9.04}, {"name": "BG Lac", "m": 8.87}, {"name": "V636 Cas", "m": 7.18},
    {"name": "T Cru", "m": 6.32}, {"name": "R Mus", "m": 6.25}
]

print("=========================================")
print("  АНАЛИЗ 50 ЦЕФЕИД С ВЫСОКОЙ ТОЧНОСТЬЮ   ")
print("=========================================")

results_summary = []

for star in stars_to_check:
    name = star["name"]
    m_v = star["m"]
    print(f"Обработка {name}...", end=" ", flush=True)

    period = analyze_cepheid(name)

    if period:
        # Применение закона Ливитта
        M_v = -2.81 * np.log10(period) - 1.43
        extinction_Av = 0.3
        distance_pc = 10 ** ((m_v - M_v + 5 - extinction_Av) / 5)

        results_summary.append(f"{name}: {distance_pc:.2f} парсек")
        print(f"[OK]")
    else:
        results_summary.append(f"{name}: Данные не найдены")
        print(f"[Пропуск]")

print("\nИТОГОВЫЙ СПИСОК РАССТОЯНИЙ:")
for res in results_summary:
    print(res)