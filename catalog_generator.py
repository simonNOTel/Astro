import pandas as pd
from astroquery.simbad import Simbad
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


def generate_target_list(limit=5000):
    print("Подключение к Simbad через TAP...")

    # Используем проверенные имена столбцов
    query = f"""
    SELECT TOP {limit}
        main_id as name, ra, dec, V as v_mag, I as i_mag, J as j_mag, K as k_mag, plx_value as parallax
    FROM basic
    WHERE 
        (main_types LIKE '%DCEP%' OR main_types LIKE '%RRLyr%')
        AND V < 13
        AND plx_value > 0
    """

    try:
        print(f"Запрос {limit} звезд...")
        result_table = Simbad.query_tap(query)
        if result_table is None: return

        df = result_table.to_pandas()
        # Декодируем имена
        df['name'] = df['name'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)

        # Сохраняем
        df.to_csv("candidates_listold.csv", index=False)
        print(f"Успех! Файл 'candidates_listold.csv' создан ({len(df)} звезд).")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    generate_target_list()