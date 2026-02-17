import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

from data_fetcher import get_star_metadata, download_lightcurve
from analysis import process_lightcurve, find_period
# Импортируем обновленные функции
from astrophysics import calculate_gaia_distance, calculate_cepheid_distance, calculate_rr_lyrae_distance
from visualizer import save_plots

# Смешанный список: Цефеиды + RR Лиры
STARS = [
    # --- Цефеиды (Гиганты, видны далеко) ---
    "RT Aur", "T Vul", "FF Aql", "S Vul", "RU Sct", "Delta Cep",
    # --- RR Лиры (Старые звезды, их много) ---
    "RR Lyr",  # Самая главная звезда этого типа
    "XZ Cyg",  # Очень быстрая пульсация
    "SU Dra",  # В гало Галактики
    "VY Ser"
]

print(
    f"{'STAR':<10} | {'PER(d)':<8} | {'TYPE':<12} | {'GAIA(pc)':<8} | {'CALC(pc)':<8} | {'Av(est)':<8} | {'STATUS':<15}")
print("-" * 90)

results = []

for star in STARS:
    # 1. Данные
    meta = get_star_metadata(star)
    if not meta: continue

    raw_lc = download_lightcurve(star)
    if raw_lc is None: continue

    # 2. Период
    clean_lc = process_lightcurve(raw_lc)
    period, pg, power = find_period(clean_lc)

    if power < 0.05: continue

    # 3. АВТОМАТИЧЕСКАЯ КЛАССИФИКАЦИЯ
    dist_calc = None
    method_name = "---"

    # Если период больше 1 дня -> Считаем как Цефеиду
    if period > 1.0:
        dist_calc, method_name = calculate_cepheid_distance(
            period, meta['v_mag'], meta['i_mag'], meta['j_mag'], meta['k_mag']
        )
    # Если период меньше 1 дня -> Считаем как RR Лиры
    else:
        dist_calc, method_name = calculate_rr_lyrae_distance(
            period, meta['v_mag'], meta['k_mag']
        )

    if dist_calc is None:
        print(f"{star:<10} | Не хватает данных")
        continue

    # 4. Сравнение с Gaia и поиск ПЫЛИ
    d_gaia = calculate_gaia_distance(meta['parallax_mas'])

    Av_estimate = 0.0
    status = "Normal"
    error_str = "---"

    if d_gaia:
        # Пытаемся оценить поглощение грубо:
        # Разница модулей расстояний (если Calc > Gaia, значит свет ослаблен пылью)
        mu_calc = 5 * np.log10(dist_calc) - 5
        mu_gaia = 5 * np.log10(d_gaia) - 5
        Av_estimate = mu_calc - mu_gaia

        if Av_estimate > 0.5:
            status = "DUST FOUND"
        elif Av_estimate < -0.3:
            status = "ANOMALY"
        else:
            status = "Clean"

        d_gaia_str = f"{d_gaia:.0f}"
    else:
        d_gaia_str = "---"
        status = "No Gaia"

    # Визуализация
    save_plots(star, clean_lc, pg, period)

    print(
        f"{star:<10} | {period:<8.3f} | {method_name:<12} | {d_gaia_str:<8} | {dist_calc:<8.0f} | {Av_estimate:<8.2f} | {status:<15}")

    results.append({
        "Star": star, "Period": period, "Type": method_name,
        "Gaia_Dist": d_gaia, "Calc_Dist": dist_calc, "Dust_Av": Av_estimate
    })

df = pd.DataFrame(results)
df.to_csv("universal_map.csv", index=False)