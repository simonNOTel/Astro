import warnings
import numpy as np
import lightkurve as lk
from astroquery.simbad import Simbad

# Отключаем надоедливые предупреждения о переименовании колонок (мы их уже учли)
warnings.filterwarnings("ignore", category=DeprecationWarning)


def get_star_metadata(star_name):
    """
    Получает V, I и параллакс, используя новые имена колонок Simbad (2024+).
    """
    # Сброс и настройка полей
    Simbad.reset_votable_fields()
    # Запрашиваем данные (Simbad вернет их в колонках 'V', 'I', 'plx_value')
    Simbad.add_votable_fields('flux(V)', 'flux(I)', 'plx')

    try:
        table = Simbad.query_object(star_name)
        if table is None:
            print(f"Simbad: Объект {star_name} не найден.")
            return None

        # --- ИЗВЛЕЧЕНИЕ ДАННЫХ ПО ТОЧНЫМ ИМЕНАМ ---

        # 1. Видимая величина V
        if 'V' in table.colnames and not np.ma.is_masked(table['V'][0]):
            v_mag = float(table['V'][0])
        else:
            print(f"Simbad: У звезды {star_name} нет данных V.")
            return None

        # 2. Инфракрасная величина I
        if 'I' in table.colnames and not np.ma.is_masked(table['I'][0]):
            i_mag = float(table['I'][0])
        else:
            # Попробуем альтернативу: иногда I называют 'R_I' или 'J'
            # Но для метода Везенайта строго нужен I.
            print(f"Simbad: У звезды {star_name} нет данных I (нужны для Wesenheit).")
            return None

        # 3. Параллакс (plx_value)
        plx = np.nan
        if 'plx_value' in table.colnames and not np.ma.is_masked(table['plx_value'][0]):
            plx = float(table['plx_value'][0])

        return {
            "v_mag": v_mag,
            "i_mag": i_mag,
            "parallax_mas": plx
        }

    except Exception as e:
        print(f"Ошибка соединения с Simbad для {star_name}: {e}")
        return None


def download_lightcurve(star_name):
    """
    Скачивание данных Kepler/TESS.
    """
    try:
        # Приоритет: Kepler
        search = lk.search_lightcurve(star_name, mission='Kepler', author='Kepler')
        # Если нет — TESS
        if len(search) == 0:
            search = lk.search_lightcurve(star_name, mission='TESS', author='SPOC')

        if len(search) == 0:
            return None

        # Берем самый длинный сет данных
        lc = search[0].download()
        return lc
    except Exception as e:
        return None