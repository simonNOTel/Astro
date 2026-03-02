import pandas as pd
import os
from astroquery.gaia import Gaia


def fetch_gaia_data():
    """
    Загружает данные из Gaia DR3.
    Использует кэширование, чтобы не зависеть от сбоев сервера.
    """
    cache_file = "raw_gaia_cache.csv"

    # 1. Проверяем, есть ли данные локально
    if os.path.exists(cache_file):
        print(f"--- Загрузка данных из локального кэша: {cache_file} ---")
        return pd.read_csv(cache_file)

    print("--- Локальный кэш не найден. Запуск запросов к серверу Gaia (ESA) ---")

    # Настройка лимитов (снятие ограничений на количество строк)
    Gaia.ROW_LIMIT = -1

    # Условия фильтрации: живой параллакс, хороший RUWE (качество) и точность > 10 сигма
    common_where = "s.parallax > 0 AND s.ruwe < 1.4 AND s.parallax/s.parallax_error > 10"

    # Запрос для Цефеид (Классические + II тип)
    query_cep = f"""
    SELECT 
        s.source_id, s.ra, s.dec, s.phot_g_mean_mag as v_mag, s.parallax, s.parallax_error,
        c.pf as period, c.type_best_classification as sub_type, 'CEP' as main_type
    FROM gaiadr3.gaia_source AS s
    JOIN gaiadr3.vari_cepheid AS c ON s.source_id = c.source_id
    WHERE {common_where}
    """

    # Запрос для RR Лир
    query_rr = f"""
    SELECT 
        s.source_id, s.ra, s.dec, s.phot_g_mean_mag as v_mag, s.parallax, s.parallax_error,
        r.pf as period, r.type_best_classification as sub_type, 'RR' as main_type
    FROM gaiadr3.gaia_source AS s
    JOIN gaiadr3.vari_rrlyrae AS r ON s.source_id = r.source_id
    WHERE {common_where}
    """

    try:
        print("Отправка запроса на Цефеиды...")
        job_cep = Gaia.launch_job_async(query_cep)
        df_cep = job_cep.get_results().to_pandas()
        print(f"Получено Цефеид: {len(df_cep)}")

        print("Отправка запроса на RR Лиры...")
        job_rr = Gaia.launch_job_async(query_rr)
        df_rr = job_rr.get_results().to_pandas()
        print(f"Получено RR Лир: {len(df_rr)}")

        # Объединяем результаты
        full_df = pd.concat([df_cep, df_rr], ignore_index=True)

        if not full_df.empty:
            # Сохраняем в кэш, чтобы не качать заново
            full_df.to_csv(cache_file, index=False)
            print(f"Данные успешно закешированы в {cache_file}")

        return full_df

    except Exception as e:
        print(f"!!! Ошибка при работе с Gaia API: {e}")
        return pd.DataFrame()  # Возвращаем пустой объект, чтобы main.py мог это обработать