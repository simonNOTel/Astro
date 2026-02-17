import pandas as pd
import numpy as np
import os
import warnings
from tqdm import tqdm

warnings.filterwarnings("ignore")

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

    candidates = pd.read_csv(INPUT_FILE)
    total_stars = len(candidates)

    # --- ОБНОВЛЕННЫЙ ЗАГОЛОВОК (RA, DEC) ---
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Star,RA,Dec,Period,Type,Gaia_Dist,Calc_Dist,Dust_Av,Status\n")
            already_processed = []
    else:
        existing = pd.read_csv(OUTPUT_FILE)
        already_processed = existing['Star'].tolist()
        print(f"Уже обработано {len(already_processed)} звезд.")

    print(f"Начинаем анализ {total_stars} звезд...")

    for index, row in tqdm(candidates.iterrows(), total=total_stars):
        star = row['Star']
        if star in already_processed: continue

        try:
            # Забираем координаты из строки
            ra = row['ra']
            dec = row['dec']

            meta = {
                'v_mag': row['v_mag'], 'i_mag': row['i_mag'],
                'j_mag': row['j_mag'], 'k_mag': row['k_mag'],
                'parallax_mas': row['parallax_mas']
            }

            raw_lc = download_lightcurve(star)
            if raw_lc is None: continue

            clean_lc = process_lightcurve(raw_lc)
            period, pg, power = find_period(clean_lc)

            if power < 0.05: continue

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

            if status != "Clean":
                save_plots(star, clean_lc, pg, period)

            # --- ЗАПИСЬ С КООРДИНАТАМИ ---
            with open(OUTPUT_FILE, 'a') as f:
                line = f"{star},{ra},{dec},{period:.4f},{method_name},{gaia_str},{dist_calc:.0f},{Av_estimate:.2f},{status}\n"
                f.write(line)

        except Exception as e:
            continue

    print("\nГотово! Карта сохранена в", OUTPUT_FILE)


if __name__ == "__main__":
    run_analysis()