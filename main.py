import pandas as pd
import numpy as np
import os
import warnings
from tqdm import tqdm

import data_fetcher
import analysis
import astrophysics
import visualizer

warnings.filterwarnings("ignore")

INPUT_FILE = "my_stars_data.csv"
OUTPUT_FILE = "universal_map_large.csv"

def run_analysis():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден!")
        return

    candidates = pd.read_csv(INPUT_FILE)
    
    # Подготовка файла результатов
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Star,RA,Dec,Period,Type,Gaia_Dist,Calc_Dist,Dust_Av,Status\n")

    print(f"Анализ {len(candidates)} звезд...")

    for index, row in tqdm(candidates.iterrows(), total=len(candidates)):
        star = str(row['name'])
        try:
            ra, dec = float(row['ra']), float(row['dec'])
            
            # Проверка спектрального типа: углеродные звезды (C) не являются Цефеидами!
            sp_type = str(row.get('sp_type', ''))
            is_carbon = 'C' in sp_type

            meta = data_fetcher.get_star_metadata(star, ra, dec)
            if not meta: continue

            # Скачивание по координатам
            raw_lc = data_fetcher.download_lightcurve(ra, dec)
            if raw_lc is None: continue

            clean_lc = analysis.process_lightcurve(raw_lc)
            period, pg, power = analysis.find_period(clean_lc)

            # Сниженный порог мощности для зашумленных данных
            if power < 0.001: continue

            # Астрофизические расчеты
            star_type = "Cepheid" if period > 1.0 else "RR Lyrae"
            
            # Если это углеродная звезда, пропускаем расчет расстояния по формуле Цефеид
            if is_carbon and star_type == "Cepheid":
                dist_calc, method_name = None, "Carbon_Star_Skip"
            elif star_type == "Cepheid":
                dist_calc, method_name = astrophysics.calculate_cepheid_distance(
                    period, meta['v_mag'], meta['i_mag'], meta['j_mag'], meta['k_mag']
                )
            else:
                dist_calc, method_name = astrophysics.calculate_rr_lyrae_distance(
                    period, meta['v_mag'], meta['k_mag']
                )

            if dist_calc is None: continue

            d_gaia = astrophysics.calculate_gaia_distance(meta['parallax_mas'])
            
            status, av_est = "Normal", 0.0
            if d_gaia:
                # Av = 5*log10(D_calc / D_gaia)
                av_est = 5 * np.log10(dist_calc / d_gaia)
                if av_est > 0.5: status = "DUST FOUND"
                elif av_est < -0.5: status = "ANOMALY"
                else: status = "Clean"

            # Сохранение графиков для подозрительных объектов
            if status != "Clean":
                visualizer.save_plots(star, clean_lc, pg, period)

            with open(OUTPUT_FILE, 'a') as f:
                f.write(f"{star},{ra},{dec},{period:.4f},{method_name},{d_gaia:.1f if d_gaia else ''},{dist_calc:.1f},{av_est:.2f},{status}\n")

        except Exception as e:
            continue

if __name__ == "__main__":
    run_analysis()
