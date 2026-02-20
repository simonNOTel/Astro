import pandas as pd
from astroquery.xmatch import XMatch
from astropy import units as u
from astropy.table import Table


def enrich_stars_with_periods(input_file, output_file):
    print(f"1. Читаем данные из файла: {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{input_file}' не найден. Убедитесь, что первый скрипт отработал корректно.")
        return

    # Убедимся, что координаты представлены в виде чисел (иногда при чтении csv возникают ошибки типов)
    df['ra'] = pd.to_numeric(df['ra'], errors='coerce')
    df['dec'] = pd.to_numeric(df['dec'], errors='coerce')

    # Создаем таблицу astropy только с нужными для поиска колонками (исключаем пустые координаты)
    clean_df = df[['name', 'ra', 'dec']].dropna()
    table_to_match = Table.from_pandas(clean_df)

    print(f"2. Запуск кросс-матчинга для {len(table_to_match)} объектов...")
    print("Ищем совпадения в каталоге VSX (VizieR: B/vsx/vsx). Это займет около 1-2 минут...")

    try:
        # Отправляем запрос на сервер CDS
        matched_table = XMatch.query(
            cat1=table_to_match,
            cat2='vizier:B/vsx/vsx',  # Каталог переменных звезд VSX
            max_distance=3 * u.arcsec,  # Ищем в радиусе 3 угловых секунд
            colRA1='ra',
            colDec1='dec'
        )

        # Превращаем результат обратно в привычный pandas DataFrame
        matched_df = matched_table.to_pandas()
        print(f"Успешно! Найдено совпадений: {len(matched_df)}")

        # В каталоге VSX нужные нам данные лежат в колонках 'Period' и 'Type'
        # Берем только их и 'name' для объединения
        match_subset = matched_df[['name', 'Period', 'Type']].copy()

        # Убираем дубликаты (на случай, если одна звезда сматчилась с двумя объектами)
        match_subset = match_subset.drop_duplicates(subset=['name'])

        # 3. Объединяем полученные данные с вашей исходной таблицей
        final_df = pd.merge(df, match_subset, on='name', how='left')

        # Переносим найденные периоды в вашу заранее созданную колонку 'period'
        final_df['period'] = final_df['Period']

        # Если в вашем файле тип звезды был не указан, берем его из каталога VSX
        final_df['sp_type'] = final_df['sp_type'].fillna(final_df['Type'])

        # Удаляем лишние колонки, оставшиеся после объединения
        final_df.drop(columns=['Period', 'Type'], inplace=True, errors='ignore')

        # 4. Сохраняем в новый файл
        final_df.to_csv(output_file, index=False)
        print(f"4. Готово! Данные сохранены в файл: '{output_file}'")

        # Выводим небольшую статистику
        found_periods = final_df['period'].notna().sum()
        print(f"ИТОГ: Период найден для {found_periods} звезд из {len(final_df)}.")

    except Exception as e:
        print(f"Произошла ошибка при обращении к серверу кросс-матчинга: {e}")


# Запуск скрипта
enrich_stars_with_periods('stars_prepared.csv', 'stars_with_periods.csv')