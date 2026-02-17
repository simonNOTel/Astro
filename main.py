import pandas as pd
import numpy as np
import os
import warnings
from tqdm import tqdm

warnings.filterwarnings("ignore")

# Импорт твоих модулей
from data_fetcher import download_lightcurve
from analysis import process_lightcurve, find_period
from astrophysics import calculate_gaia_distance, calculate_cepheid_distance, calculate_rr_lyrae_distance
from visualizer import save_plots

INPUT_FILE = "candidates_list.csv"
OUTPUT_FILE = "universal_map_large.csv"


def run_analysis():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден! Запусти catalog_generator.py")
        return

    # Загружаем данные
    candidates = pd.read_csv(INPUT_FILE)

    # --- УЛУЧШЕННЫЙ ПОИСК КОЛОНОК ---
    def find_col(possible_names):
        for name in possible_names:
            for col in candidates.columns:
                if col.lower() == name.lower():
                    return col
        return None

    # Ищем колонку со звездой (добавил 'name')
    star_col = find_col(['name', 'Star', 'main_id', 'star'])
    ra_col = find_col(['ra', 'ra_d'])
    dec_col = find_col(['dec', 'dec_d'])

    if not star_col:
        print(f"ОШИБКА: Не найдена колонка с названием звезды! Колонки: {candidates.columns.tolist()}")
        return

    total_stars = len(candidates)

    # Подготовка выходного файла
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("Star,RA,Dec,Period,Type,Gaia_Dist,Calc_Dist,Dust_Av,Status\n")
            already_processed = []
    else:
        try:
            existing = pd.read_csv(OUTPUT_FILE)
            already_processed = existing['Star'].astype(str).tolist()
            print(f"Уже обработано {len(already_processed)} звезд.")
        except:
            already_processed = []

    print(f"Начинаем анализ {total_stars} звезд...")

    for index, row in tqdm(candidates.iterrows(), total=total_stars):
        star = str(row[star_col])
        if star in already_processed:
            continue

        try:
            ra = row[ra_col] if ra_col else 0
            dec = row[dec_col] if dec_col else 0

            # Авто-поиск метаданных под твой файл
            def get_val(names):
                c = find_col(names)
                return row[c] if c and not pd.isna(row[c]) else None

            meta = {
                'v_mag': get_val(['v_mag', 'V']),
                'i_mag': get_val(['i_mag', 'I']),
                'j_mag': get_val(['j_mag', 'J']),
                'k_mag': get_val(['k_mag', 'K']),
                'parallax_mas': get_val(['parallax', 'parallax_mas', 'plx_value'])
            }

            # 1. Загрузка данных
            raw_lc = download_lightcurve(star)
            if raw_lc is None: continue

            # 2. Поиск периода
            clean_lc = process_lightcurve(raw_lc)
            period, pg, power = find_period(clean_lc)

            if power < 0.05: continue

            # 3. Расчет расстояния
            dist_calc = None
            method_name = "---"

            if period > 1.0:
                dist_calc, method_name = calculate_cepheid_distance(
                    period, meta['v_mag'], meta['i_mag'], meta['j_mag'], meta['k_mag']
                )
            else:
                dist_calc, method_name = calculate_rr_lyrae_distance(
                    period, meta['v_mag'], meta['k_mag']
                )

            if dist_calc is None: continue

            # 4. Сравнение с Gaia
            d_gaia = calculate_gaia_distance(meta['parallax_mas'])

            Av_estimate = 0.0
            status = "Normal"
            gaia_str = ""

            if d_gaia:
                mu_calc = 5 * np.log10(dist_calc) - 5
                mu_gaia = 5 * np.log10(d_gaia) - 5
                Av_estimate = mu_calc - mu_gaia

                if Av_estimate > 0.5:
                    status = "DUST FOUND"
                elif Av_estimate < -0.3:
                    status = "ANOMALY"
                else:
                    status = "Clean"
                gaia_str = f"{d_gaia:.0f}"
            else:
                status = "No Gaia"

            # 5. Сохранение графиков
            if status != "Clean":
                save_plots(star, clean_lc, pg, period)

            # 6. Запись результата
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                line = f"{star},{ra},{dec},{period:.4f},{method_name},{gaia_str},{dist_calc:.0f},{Av_estimate:.2f},{status}\n"
                f.write(line)

        except Exception as e:
            continue

    print(f"\nГотово! Результаты в {OUTPUT_FILE}")


if __name__ == "__main__":
    run_analysis()
