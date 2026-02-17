import pyvo as vo
import pandas as pd
import numpy as np
import warnings

# Отключаем предупреждения
warnings.filterwarnings("ignore")


def get_final_catalog():
    print("=== СОЗДАНИЕ ИТОГОВОГО КАТАЛОГА (TAP ЗАПРОС) ===")

    # Подключение к SIMBAD
    service_url = "http://simbad.u-strasbg.fr/simbad/sim-tap"
    service = vo.dal.TAPService(service_url)

    # Мы запрашиваем всё сразу: Спектральный тип, Координаты (они сразу в градусах), Параллаксы
    # Нам не нужно читать stars.txt, мы используем те же критерии фильтрации, что и раньше.

    query = """
    SELECT TOP 20000 
        basic.main_id as name, 
        basic.ra, 
        basic.dec, 
        basic.sp_type, 
        flux.flux AS v_mag, 
        basic.plx_value as parallax,
        basic.plx_err as plx_error
    FROM basic
    JOIN flux ON basic.oid = flux.oidref
    WHERE 
        flux.filter = 'V'
        AND flux.flux < 14.0
        AND basic.plx_value > 0
        AND basic.otype IN (
            'DCEP', 'DCEPS', 'Cep', 'C*', 
            'CW', 'CWA', 'CWB', 'pW',
            'RRLyr', 'RR*', 'RRAB', 'RRC', 'RR(B)'
        )
    ORDER BY v_mag ASC
    """

    print("Отправка запроса... (Ждите 10-20 секунд)")

    try:
        # Выполняем запрос
        result = service.search(query)
        # Превращаем сразу в Pandas DataFrame
        df = result.to_table().to_pandas()

        print(f"-> Получено звезд: {len(df)}")

        # --- ОБРАБОТКА ДАННЫХ (PANDAS) ---
        # Это работает мгновенно для всей таблицы, без циклов

        # 1. Декодируем байтовые строки (b'Name' -> 'Name')
        for col in ['name', 'sp_type']:
            if df[col].dtype == object:
                # Если внутри байты, декодируем. Если строки - оставляем.
                try:
                    df[col] = df[col].str.decode('utf-8')
                except:
                    pass

        # 2. Считаем SNR (Сигнал/Шум)
        # Создаем колонку snr, заполняем нулями
        df['snr'] = 0.0

        # Там где ошибка > 0, считаем деление
        valid_idx = (df['plx_error'] > 0) & (df['plx_error'].notna())
        df.loc[valid_idx, 'snr'] = df.loc[valid_idx, 'parallax'] / df.loc[valid_idx, 'plx_error']

        # Округляем
        df['snr'] = df['snr'].round(2)

        # 3. Флаг надежности (reliable)
        df['reliable'] = df['snr'] > 5

        # 4. Вывод статистики
        reliable_count = len(df[df['reliable'] == True])
        print("-" * 40)
        print(f"Всего объектов: {len(df)}")
        print(f"Надежных (SNR > 5): {reliable_count}")
        print("-" * 40)

        # 5. Сохранение
        filename = 'my_stars_data.csv'
        df.to_csv(filename, index=False)
        print(f"Файл сохранен: {filename}")

        # Пример
        print("\nПервые 5 строк:")
        print(df[['name', 'ra', 'v_mag', 'snr', 'reliable', 'sp_type']].head())

    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        if hasattr(e, 'content'):
            print(f"Детали сервера: {e.content}")


if __name__ == "__main__":
    get_final_catalog()