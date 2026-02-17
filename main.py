import pandas as pd
import numpy as np
import os
import warnings
from tqdm import tqdm
import time

import data_fetcher
import analysis
import visualizer
import astrophysics

warnings.filterwarnings("ignore")

INPUT_FILE = 'my_stars_data.csv'
OUTPUT_FILE = 'universal_map_large.csv'
PLOTS_DIR = 'plots/'


def main():
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)

    print(f"--- ЗАПУСК АНАЛИЗА (v2.0 Fixed) ---")

    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"Загружено звезд: {len(df)}")
    except FileNotFoundError:
        print(f"Файл {INPUT_FILE} не найден.")
        return

    headers = "name,ra,dec,star_type,period_days,distance_calc,distance_gaia,extinction_Av,method_used,status\n"
    with open(OUTPUT_FILE, 'w') as f:
        f.write(headers)

    for index, row in tqdm(df.iterrows(), total=df.shape[0], unit="star"):
        star_name = str(row['name'])

        try:
            # 1. Координаты
            try:
                ra = float(row['ra'])
                dec = float(row['dec'])
                csv_parallax = float(row['parallax']) if 'parallax' in row and not np.isnan(row['parallax']) else None
                csv_v_mag = float(row['v_mag']) if 'v_mag' in row and not np.isnan(row['v_mag']) else None
            except:
                continue

            # 2. Метаданные (передаем RA/DEC, чтобы Simbad нашел по координатам!)
            metadata = data_fetcher.get_star_metadata(star_name, ra=ra, dec=dec)

            if metadata:
                v_mag = metadata['v_mag'] if metadata['v_mag'] else csv_v_mag
                i_mag = metadata['i_mag']
                j_mag = metadata['j_mag']
                k_mag = metadata['k_mag']
                parallax = csv_parallax if csv_parallax else metadata['parallax_mas']
            else:
                v_mag = csv_v_mag
                i_mag = j_mag = k_mag = None
                parallax = csv_parallax

            # 3. Скачивание (TESS/Kepler)
            lc_raw = data_fetcher.download_lightcurve(ra, dec)
            if lc_raw is None:
                continue

                # 4. Анализ
            lc_clean = analysis.process_lightcurve(lc_raw)
            if lc_clean is None:
                continue

            period, pg, power = analysis.find_period(lc_clean)

            # ИСПРАВЛЕНИЕ: Снизили порог с 0.05 до 0.001
            # Реальные данные шумные, 0.05 отсеивает почти всё.
            if power < 0.001:
                continue

            # 5. Астрофизика
            star_type = "Cepheid" if period > 1.0 else "RR Lyrae"
            dist_gaia = astrophysics.calculate_gaia_distance(parallax)

            dist_calc = None
            method_used = "Unknown"

            if star_type == "Cepheid":
                dist_calc, method_used = astrophysics.calculate_cepheid_distance(period, v_mag, i_mag, j_mag, k_mag)
            else:
                dist_calc, method_used = astrophysics.calculate_rr_lyrae_distance(period, v_mag, k_mag)

            if dist_calc is None:
                continue

            # 6. Статус
            status = "Clean"
            extinction_Av = 0.0

            if dist_gaia is not None and dist_gaia > 0:
                try:
                    extinction_Av = 5 * np.log10(dist_calc / dist_gaia)
                except:
                    extinction_Av = 0

                if extinction_Av > 0.5:
                    status = "DUST FOUND"
                elif extinction_Av < -0.5:
                    status = "ANOMALY"
            else:
                status = "No Gaia Ref"

            # 7. Запись
            result_line = f"{star_name},{ra},{dec},{star_type},{period:.5f},{dist_calc:.2f}," \
                          f"{dist_gaia if dist_gaia else ''},{extinction_Av:.3f},{method_used},{status}\n"

            with open(OUTPUT_FILE, 'a') as f:
                f.write(result_line)

            # 8. Графики
            if status in ["DUST FOUND", "ANOMALY"]:
                try:
                    visualizer.save_plots(star_name, lc_clean, pg, period)
                except:
                    pass

        except KeyboardInterrupt:
            break
        except Exception:
            continue

    print(f"\n>>> Готово! Результаты в {OUTPUT_FILE}")


if __name__ == "__main__":
    main()