import pandas as pd
import numpy as np
import warnings
import data_fetcher
import analysis
import astrophysics

# Отключаем лишние предупреждения для чистоты вывода
warnings.filterwarnings("ignore")

# Список тестовых объектов
# 1. V* U Hya — углеродная звезда (проверка нового фильтра пропуска)
# 2. RR Lyrae — эталон для проверки скачивания и периода
test_candidates = [
    {"name": "V* U Hya", "ra": 159.388637, "dec": -13.384542, "sp_type": "C-N5"},
    {"name": "RR Lyrae", "ra": 290.240000, "dec": 42.795900, "sp_type": "A8"}
]


def run_local_test():
    print("=== ЗАПУСК ЛОКАЛЬНОГО ТЕСТА (PC) ===")

    for star_data in test_candidates:
        star_name = star_data['name']
        ra = star_data['ra']
        dec = star_data['dec']
        sp_type = star_data['sp_type']

        print(f"\n[STATION 1] Обработка: {star_name}")
        print(f"    RA: {ra}, Dec: {dec}, SpType: {sp_type}")

        # Шаг 1: Метаданные из Simbad
        meta = data_fetcher.get_star_metadata(star_name, ra, dec)
        if not meta:
            print("    [!] ОШИБКА: Simbad не вернул данные. Проверьте интернет.")
            continue
        print(f"    [OK] Simbad: V={meta.get('v_mag')}, K={meta.get('k_mag')}, Plx={meta.get('parallax_mas')}")

        # Шаг 2: Скачивание кривой блеска
        print("    [2] Скачивание из MAST...")
        raw_lc = data_fetcher.download_lightcurve(ra, dec)
        if raw_lc is None:
            print("    [!] ПРОПУСК: Кривая блеска не найдена в архивах TESS/Kepler.")
            continue
        print(f"    [OK] MAST: Скачано точек: {len(raw_lc)}")

        # Шаг 3: Очистка и Период
        lc_clean = analysis.process_lightcurve(raw_lc)
        period, pg, power = analysis.find_period(lc_clean)
        print(f"    [3] Анализ: Period={period:.4f} d, Power={power:.5f}")

        if power < 0.001:
            print(f"    [!] ПРОПУСК: Слишком слабый сигнал (Power < 0.001)")
            continue

        # Шаг 4: Астрофизика и проверка на углеродные звезды
        star_type = "Cepheid" if period > 1.0 else "RR Lyrae"
        is_carbon = 'C' in sp_type

        dist_calc = None
        method_name = "---"

        if is_carbon and star_type == "Cepheid":
            print("    [i] ИНФО: Углеродная звезда. Пропускаем расчет по формуле Цефеид (избегаем ANOMALY).")
            method_name = "Carbon_Star_Skip"
        elif star_type == "Cepheid":
            dist_calc, method_name = astrophysics.calculate_cepheid_distance(
                period, meta['v_mag'], meta.get('i_mag'), meta.get('j_mag'), meta['k_mag']
            )
        else:
            dist_calc, method_name = astrophysics.calculate_rr_lyrae_distance(
                period, meta['v_mag'], meta['k_mag']
            )

        # Шаг 5: Сравнение с Gaia
        d_gaia = astrophysics.calculate_gaia_distance(meta['parallax_mas'])

        if dist_calc:
            av_est = 5 * np.log10(dist_calc / d_gaia) if d_gaia else 0
            status = "Clean"
            if av_est > 0.5:
                status = "DUST FOUND"
            elif av_est < -0.5:
                status = "ANOMALY"

            print(f"    [RESULT] Метод: {method_name}")
            print(f"    [RESULT] Dist_Calc: {dist_calc:.1f} pc, Dist_Gaia: {d_gaia if d_gaia else 'N/A'}")
            print(f"    [RESULT] Av: {av_est:.2f}, Status: {status}")
        else:
            print(f"    [!] РЕЗУЛЬТАТ: Расстояние не рассчитано (Method: {method_name})")

    print("\n=== ТЕСТ ЗАВЕРШЕН ===")


if __name__ == "__main__":
    run_local_test()