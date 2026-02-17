import warnings
import numpy as np
import lightkurve as lk
from astroquery.simbad import Simbad

warnings.filterwarnings("ignore", category=DeprecationWarning)


def get_star_metadata(star_name):
    """
    Скачивает фотометрию в Optical (V, I) и Infrared (J, K) диапазонах.
    """
    Simbad.reset_votable_fields()
    # Запрашиваем V, I (оптика) и J, K (инфракрасный 2MASS)
    Simbad.add_votable_fields('flux(V)', 'flux(I)', 'flux(J)', 'flux(K)', 'plx')

    try:
        table = Simbad.query_object(star_name)
        if table is None:
            print(f"Simbad: Объект {star_name} не найден.")
            return None

        # Вспомогательная функция для извлечения
        def get_val(col_name):
            if col_name in table.colnames and not np.ma.is_masked(table[col_name][0]):
                return float(table[col_name][0])
            return None

        # Собираем всё, что есть
        data = {
            "v_mag": get_val('V'),
            "i_mag": get_val('I'),
            "j_mag": get_val('J'),  # Инфракрасный 1.2 мкм
            "k_mag": get_val('K'),  # Инфракрасный 2.2 мкм
            "parallax_mas": get_val('plx_value')
        }

        # Проверка: если вообще ничего нет
        if all(v is None for v in [data['v_mag'], data['j_mag']]):
            print(f"CRITICAL: У {star_name} нет ни оптической, ни ИК фотометрии.")
            return None

        return data

    except Exception as e:
        print(f"Ошибка Simbad для {star_name}: {e}")
        return None


def download_lightcurve(star_name):
    """Скачивание данных Kepler/TESS."""
    try:
        search = lk.search_lightcurve(star_name, mission='Kepler', author='Kepler')
        if len(search) == 0:
            search = lk.search_lightcurve(star_name, mission='TESS', author='SPOC')

        if len(search) == 0:
            return None
        return search[0].download()
    except:
        return None