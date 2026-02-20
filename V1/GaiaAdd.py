import pandas as pd
import numpy as np
from astropy.table import Table
from astroquery.gaia import Gaia

# 1. Загружаем ваш файл
input_file = 'final_universal_map.csv'
df = pd.read_csv(input_file)

# Проверяем, что координаты имеют числовой формат (защита от ошибок)
df['RA'] = pd.to_numeric(df['RA'], errors='coerce')
df['Dec'] = pd.to_numeric(df['Dec'], errors='coerce')

# 2. Подготавливаем таблицу для отправки на сервер Gaia
# Нам нужны только имя и координаты, чтобы не гонять лишний трафик
upload_df = df[['Star', 'RA', 'Dec']].dropna()

# Конвертируем pandas DataFrame в формат astropy Table (требование astroquery)
upload_table = Table.from_pandas(upload_df)

print(f"Отправляем {len(upload_table)} объектов на сервер Gaia для Cross-match...")

# 3. Пишем ADQL запрос с использованием JOIN
# tap_upload.my_table - это наша временно загруженная таблица
# Ищем совпадения в радиусе 2 угловых секунд (2./3600. градусов)
query = """
SELECT 
    user_tab.Star, 
    gaia.parallax AS gaia_parallax, 
    gaia.parallax_error AS gaia_plx_error, 
    gaia.phot_g_mean_mag
FROM tap_upload.my_table AS user_tab
JOIN gaiadr3.gaia_source AS gaia
  ON 1=CONTAINS(
         POINT('ICRS', user_tab.RA, user_tab.Dec),
         CIRCLE('ICRS', gaia.ra, gaia.dec, 2./3600.)
     )
"""

# 4. Выполняем асинхронный запрос (надежнее для больших объемов)
# Сервер сам сопоставит наши координаты со своей базой
try:
    job = Gaia.launch_job_async(
        query=query,
        upload_resource=upload_table,
        upload_table_name="my_table"
    )

    # Получаем результаты
    results = job.get_results()
    print(f"Успех! Найдено совпадений в Gaia: {len(results)}")

    # Конвертируем ответ обратно в pandas DataFrame
    df_gaia = results.to_pandas()

except Exception as e:
    print(f"Ошибка при запросе к Gaia: {e}")
    exit()

# 5. Обработка результатов из Gaia
# Иногда в радиус 2 секунд попадает несколько звезд (оптические двойные).
# Оставим самую яркую (с минимальным значением phot_g_mean_mag)
df_gaia = df_gaia.sort_values('phot_g_mean_mag').drop_duplicates(subset=['Star'], keep='first')

# Оставляем только нужные колонки перед слиянием
df_gaia = df_gaia[['Star', 'gaia_parallax', 'gaia_plx_error']]

# 6. Склеиваем данные Gaia с вашей основной таблицей
# how='left' гарантирует, что мы не потеряем ни одну из ваших исходных 5518 звезд
final_df = pd.merge(df, df_gaia, on='Star', how='left')

# 7. Считаем дистанцию по данным Gaia
# (Только для тех звезд, где параллакс найден и он больше нуля)
final_df['Gaia_Dist_Calc'] = np.where(
    final_df['gaia_parallax'] > 0,
    1000 / final_df['gaia_parallax'],
    np.nan
)
final_df['Gaia_Dist_Calc'] = final_df['Gaia_Dist_Calc'].round(2)

# 8. Сохраняем итоговый результат
output_file = 'candidates_list.csv'
final_df.to_csv(output_file, index=False)

print(f"\nГотово! Результат сохранен в файл '{output_file}'.")
print("Сравните ваши расчеты 'Calc_Dist' с новыми 'Gaia_Dist_Calc'!")