import pandas as pd
from astroquery.gaia import Gaia


def download_unlimited_gaia_dataset():
    print("1. Подключаемся к архиву космического телескопа Gaia (ESA)...")
    print("ВНИМАНИЕ: Сняты все лимиты. Мы качаем Big Data. Это может занять 3-5 минут!")

    # Запрос 1: Ищем ВСЕ качественные Цефеиды
    query_cep = """
    SELECT 
        s.source_id AS name,
        s.ra, s.dec,
        s.phot_g_mean_mag AS v_mag,
        s.parallax,
        c.pf AS period,
        'CEP' AS sp_type
    FROM gaiadr3.gaia_source AS s
    JOIN gaiadr3.vari_cepheid AS c ON s.source_id = c.source_id
    WHERE s.parallax > 0 
      AND c.pf > 0
    """

    # Запрос 2: Ищем ВСЕ качественные RR Лиры
    query_rr = """
    SELECT 
        s.source_id AS name,
        s.ra, s.dec,
        s.phot_g_mean_mag AS v_mag,
        s.parallax,
        r.pf AS period,
        'RR' AS sp_type
    FROM gaiadr3.gaia_source AS s
    JOIN gaiadr3.vari_rrlyrae AS r ON s.source_id = r.source_id
    WHERE s.parallax > 0 
      AND s.parallax / s.parallax_error > 5
      AND r.pf > 0
    """

    print("2. Отправляем запрос на Цефеиды. Ждем ответа сервера...")
    job_cep = Gaia.launch_job_async(query_cep)
    df_cep = job_cep.get_results().to_pandas()
    print(f"Получено идеальных Цефеид: {len(df_cep)}")

    print("3. Отправляем запрос на огромный массив RR Лиры. Ждем ответа сервера...")
    job_rr = Gaia.launch_job_async(query_rr)
    df_rr = job_rr.get_results().to_pandas()
    print(f"Получено идеальных RR Лиры: {len(df_rr)}")

    print("4. Объединяем и переводим параллаксы в парсеки...")
    df_total = pd.concat([df_cep, df_rr], ignore_index=True)

    # Параллакс в Gaia в миллисекундах дуги. 1000 / plx = Расстояние в парсеках.
    df_total['dist_ref'] = 1000.0 / df_total['parallax']

    output_file = 'stars_with_periods.csv'
    df_total.to_csv(output_file, index=False)

    print(f"\nАБСОЛЮТНЫЙ УСПЕХ! Скачано {len(df_total)} звезд!")
    print(f"Файл '{output_file}' готов. Можно запускать расчеты!")


# Запуск
if __name__ == '__main__':
    download_unlimited_gaia_dataset()