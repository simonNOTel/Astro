import pandas as pd
import warnings

# Скрываем лишний шум от библиотек
warnings.filterwarnings("ignore")

from data_fetcher import get_star_metadata, download_lightcurve
from analysis import process_lightcurve, find_period
from astrophysics import calculate_wesenheit_distance, calculate_basic_distance, calculate_gaia_distance
from visualizer import save_plots

STARS = [
    "RT Aur", "Zeta Gem", "FF Aql", "T Vul", "SU Cyg",
    "S Vul", "RU Sct", "X Cyg", "V350 Sgr"  # Добавил парочку для теста
]

print(f"{'STAR':<10} | {'PER(d)':<8} | {'DIST(pc)':<8} | {'METHOD':<10} | {'GAIA':<8} | {'ERR(%)':<6}")
print("-" * 75)

results = []

for star in STARS:
    # 1. Получение данных
    meta = get_star_metadata(star)
    if not meta:
        continue  # Simbad не нашел звезду вообще

    raw_lc = download_lightcurve(star)
    if raw_lc is None:
        print(f"{star:<10} | Нет данных телескопа (Kepler/TESS)")
        continue

    # 2. Анализ периода
    clean_lc = process_lightcurve(raw_lc)
    period, pg, power = find_period(clean_lc)

    if power < 0.05:  # Понизил порог чувствительности
        print(f"{star:<10} | {period:<8.3f} | Сигнал слаб/шум")
        continue

    # 3. Физика: Выбор метода
    dist_calc = calculate_wesenheit_distance(period, meta['v_mag'], meta['i_mag'])
    method_used = "Wesenheit"

    # ЕСЛИ ВЕЗЕНАЙТ НЕ СРАБОТАЛ (нет I_mag), ВКЛЮЧАЕМ ПЛАН Б
    if dist_calc is None:
        dist_calc = calculate_basic_distance(period, meta['v_mag'])
        method_used = "Basic(V)"

    dist_ref = calculate_gaia_distance(meta['parallax_mas'])

    # 4. Визуализация и вывод
    save_plots(star, clean_lc, pg, period)

    error_str = "---"
    gaia_str = "---"

    if dist_ref:
        error = abs(dist_calc - dist_ref) / dist_ref * 100
        error_str = f"{error:.1f}"
        gaia_str = f"{dist_ref:.0f}"

    print(f"{star:<10} | {period:<8.3f} | {dist_calc:<8.0f} | {method_used:<10} | {gaia_str:<8} | {error_str:<6}")

    results.append({
        "Star": star,
        "Period": period,
        "Distance": dist_calc,
        "Method": method_used,
        "Gaia_Ref": dist_ref,
        "Error": error_str
    })

df = pd.DataFrame(results)
df.to_csv("final_results.csv", index=False)
print("\nГотово! Проверь папку plots и файл final_results.csv")