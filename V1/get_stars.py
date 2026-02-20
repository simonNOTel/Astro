import pyvo as vo
import pandas as pd
import warnings

# Отключаем предупреждения
warnings.filterwarnings("ignore")


def get_stars_production():
    print("=== ЗАГРУЗКА ДАННЫХ SIMBAD (Production) ===")

    service_url = "http://simbad.u-strasbg.fr/simbad/sim-tap"
    service = vo.dal.TAPService(service_url)

    # -----------------------------------------------------------
    # ИСПРАВЛЕННЫЙ ЗАПРОС
    # -----------------------------------------------------------
    # 1. basic.plx_err - правильное название колонки ошибки
    # 2. flux.flux AS v_mag - псевдоним для сортировки
    # 3. basic.otype IN (...) - широкий поиск типов
    # -----------------------------------------------------------

    query = """
    SELECT TOP 20000 
        basic.main_id, 
        basic.ra, 
        basic.dec, 
        basic.otype, 
        flux.flux AS v_mag, 
        basic.plx_value,
        basic.plx_err
    FROM basic
    JOIN flux ON basic.oid = flux.oidref
    WHERE 
        flux.filter = 'V'                     -- Фильтр V
        AND flux.flux < 14.0                  -- Яркость до 14 mag
        AND basic.plx_value > 0               -- Параллакс существует
        AND basic.otype IN (
            'DCEP', 'DCEPS', 'Cep', 'C*',     -- Цефеиды
            'CW', 'CWA', 'CWB', 'pW',         -- Цефеиды II типа
            'RRLyr', 'RR*', 'RRAB', 'RRC', 'RR(B)' -- RR Лиры
        )
    ORDER BY v_mag ASC
    """

    print("Отправка запроса... (это может занять 10-30 секунд)")

    try:
        result = service.search(query)
        table = result.to_table()
        df = table.to_pandas()

        count = len(df)
        print(f"-> УСПЕХ! Найдено звезд: {count}")

        if count == 0:
            print("Список пуст. Проверьте соединение или критерии.")
            return

        # 1. Сохраняем список имен (stars.txt)
        txt_filename = 'stars.txt'
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for name in df['main_id']:
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                f.write(f"{name}\n")

        # 2. Сохраняем полную таблицу данных (stars_data.csv)
        # В ней теперь есть plx_err - обязательно используйте её для фильтрации шума!
        csv_filename = 'stars_data.csv'
        df.to_csv(csv_filename, index=False)

        print(f"\nДанные сохранены:")
        print(f" [1] {txt_filename} (список имен для TESS)")
        print(f" [2] {csv_filename} (таблица с RA, DEC, PLX, ERR для вашей карты)")

        print("\nПример полученных данных:")
        print(df[['main_id', 'v_mag', 'plx_value', 'plx_err']].head())

    except Exception as e:
        print(f"\nОШИБКА: {e}")
        if hasattr(e, 'content'):
            print(f"Детали: {e.content}")


if __name__ == "__main__":
    get_stars_production()