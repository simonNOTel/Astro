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

INPUT_FILE = "candidates_listold.csv"
OUTPUT_FILE = "universal_map_large.csv"


def run_analysis():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден!")
        return

    candidates = pd.read_csv(INPUT_FILE)

    # Авто-поиск колонок (Star/name, Parallax/plx)
    def find_col(possible):
        for p in possible:
            for c in candidates.columns:
                if c.lower() == p.lower(): return c
        return None

    star_col = find_col(['name', 'star', 'main_id'])
    plx_col = find_col(['parallax', 'plx_value', 'plx'])

    if not star_col:
        print(f"Ошибка: не найдена колонка с именем звезды. Есть: {candidates.columns.tolist()}")
        return

    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("Star,RA,Dec,Period,Type,Gaia_Dist,Calc_Dist,Dust_Av,Status\n")
            processed = []
    else:
        try:
            processed = pd.read_csv(OUTPUT_FILE)['Star'].astype(str).tolist()
        except:
            processed = []

    print(f"Анализ {len(candidates)} звезд...")

    for _, row in tqdm(candidates.iterrows(), total=len(candidates)):
        star = str(row[star_col])
        if star in processed: continue

        try:
            meta = {
                'v_mag': row.get('v_mag', np.nan),
                'i_mag': row.get('i_mag', np.nan),
                'j_mag': row.get('j_mag', np.nan),
                'k_mag': row.get('k_mag', np.nan),
                'parallax_mas': row.get(plx_col, np.nan)
            }

            raw_lc = download_lightcurve(star)
            if raw_lc is None: continue

            clean_lc = process_lightcurve(raw_lc)
            period, pg, power = find_period(clean_lc)
            if power < 0.05: continue

            # Выбор метода
            if period > 1.0:
                dist_calc, method = calculate_cepheid_distance(period, meta['v_mag'], meta['i_mag'], meta['j_mag'],
                                                               meta['k_mag'])
            else:
                dist_calc, method = calculate_rr_lyrae_distance(period, meta['v_mag'], meta['k_mag'])

            if not dist_calc: continue

            d_gaia = calculate_gaia_distance(meta['parallax_mas'])
            av, status = 0.0, "Normal"

            if d_gaia:
                av = (5 * np.log10(dist_calc) - 5) - (5 * np.log10(d_gaia) - 5)
                status = "DUST FOUND" if av > 0.5 else ("ANOMALY" if av < -0.3 else "Clean")

            if status != "Clean":
                save_plots(star, clean_lc, pg, period)

            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(
                    f"{star},{row.get('ra', 0)},{row.get('dec', 0)},{period:.4f},{method},{d_gaia or 0:.0f},{dist_calc:.0f},{av:.2f},{status}\n")

        except:
            continue


if __name__ == "__main__":
    run_analysis()