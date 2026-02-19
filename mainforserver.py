import pandas as pd
import numpy as np
import os
import warnings
from tqdm import tqdm

import data_fetcher
import analysis
import astrophysics
import visualizer

# Игнорируем предупреждения библиотек
warnings.filterwarnings("ignore")

INPUT_FILE = "candidates_listold.csv"
OUTPUT_FILE = "universal_map_largePC.csv"

def run_analysis():
    if not os.path.exists(INPUT_FILE):
        print(f"ОШИБКА: Файл {INPUT_FILE} не найден в папке проекта!")
        return

    candidates = pd.read_csv(INPUT_FILE).iloc[::-1]
    
    # Создаем заголовки, если файла еще нет
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Star,RA,Dec,Period,Method,Gaia_Dist,Calc_Dist,Dust_Av,Status\n")

    print(f"Начинаю анализ {len(candidates)} звезд...")

    for index, row in tqdm(candidates.iterrows(), total=len(candidates)):
        star = str(row['name'])
        try:
            ra, dec = float(row['ra']), float(row['dec'])
            sp_type = str(row.get('sp_type', ''))
            is_carbon = 'C' in sp_type

            # 1. Запрос метаданных
            meta = data_fetcher.get_star_metadata(star, ra, dec)
            if not meta:
                # print(f"-> {star}: Пропуск (Simbad не ответил)")
                continue

            # 2. Скачивание данных TESS/Kepler
            raw_lc = data_fetcher.download_lightcurve(ra, dec)
            if raw_lc is None:
                # print(f"-> {star}: Пропуск (Данные TESS не найдены)")
                continue

            # 3. Анализ периода
            clean_lc = analysis.process_lightcurve(raw_lc)
            period, pg, power = analysis.find_period(clean_lc)

            # Если сигнал очень слабый
            if power < 0.001:
                # print(f"-> {star}: Пропуск (Слабый сигнал: {power:.5f})")
                continue

            # 4. Астрофизика
            star_type = "Cepheid" if period > 1.0 else "RR Lyrae"
            dist_calc = None
            method_name = "None"
            status = "Processing"
            av_est = 0.0

            # Логика классификации
            if is_carbon and star_type == "Cepheid":
                method_name = "Carbon_Star_Skip"
                status = "Skipped (Carbon)"
            elif star_type == "Cepheid":
                dist_calc, method_name = astrophysics.calculate_cepheid_distance(
                    period, meta['v_mag'], meta.get('i_mag'), meta.get('j_mag'), meta['k_mag']
                )
            else:
                dist_calc, method_name = astrophysics.calculate_rr_lyrae_distance(
                    period, meta['v_mag'], meta['k_mag']
                )

            # 5. Сравнение с Gaia
            d_gaia = astrophysics.calculate_gaia_distance(meta['parallax_mas'])
            
            if dist_calc and d_gaia:
                av_est = 5 * np.log10(dist_calc / d_gaia)
                if av_est > 0.5: status = "DUST FOUND"
                elif av_est < -0.5: status = "ANOMALY"
                else: status = "Clean"
            elif dist_calc:
                status = "No Gaia Ref"
            
            # 6. ЗАПИСЬ В ФАЙЛ (Теперь она срабатывает всегда для найденных звезд)
            calc_val = f"{dist_calc:.1f}" if dist_calc else "0"
            gaia_val = f"{d_gaia:.1f}" if d_gaia else ""
            
            with open(OUTPUT_FILE, 'a') as f:
                f.write(f"{star},{ra},{dec},{period:.4f},{method_name},{gaia_val},{calc_val},{av_est:.2f},{status}\n")

            # Сохраняем графики только для интересных случаев
            if status in ["DUST FOUND", "ANOMALY"]:
                visualizer.save_plots(star, clean_lc, pg, period)

        except Exception as e:
            # Если возникла ошибка, мы хотя бы узнаем о ней в консоли
            print(f"\n[!] Ошибка на звезде {star}: {e}")
            continue

    print(f"\nАнализ завершен. Результаты сохранены в {OUTPUT_FILE}")

if __name__ == "__main__":
    run_analysis()
