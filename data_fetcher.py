import warnings
import numpy as np
import lightkurve as lk
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u

# Игнорируем специфические предупреждения
warnings.filterwarnings("ignore")


def get_star_metadata(star_name, ra=None, dec=None):
    """
    Скачивает фотометрию.
    Если переданы RA/DEC, ищет по координатам (это надежнее).
    Иначе ищет по имени.
    """
    Simbad.reset_votable_fields()
    Simbad.add_votable_fields('flux(V)', 'flux(I)', 'flux(J)', 'flux(K)', 'plx')

    try:
        table = None

        # 1. Приоритет: Поиск по координатам (Radius 5 arcsec)
        if ra is not None and dec is not None:
            try:
                coords = SkyCoord(ra, dec, unit=(u.deg, u.deg))
                # Ищем ближайший объект в радиусе 5 секунд
                table = Simbad.query_region(coords, radius=5 * u.arcsec)
            except:
                table = None

        # 2. Если по координатам пусто, пробуем по имени
        if table is None:
            table = Simbad.query_object(star_name)

        if table is None:
            return None

        # Берем первую строку (самый близкий объект)
        row = table[0]

        def get_val(col_name):
            if col_name in table.colnames and not np.ma.is_masked(row[col_name]):
                return float(row[col_name])
            return None

        data = {
            "v_mag": get_val('FLUX_V'),  # Simbad возвращает FLUX_V при query_region
            "i_mag": get_val('FLUX_I'),
            "j_mag": get_val('FLUX_J'),
            "k_mag": get_val('FLUX_K'),
            "parallax_mas": get_val('PLX_VALUE')
        }

        # Если ключи называются иначе (иногда бывает V вместо FLUX_V при поиске по имени)
        if data['v_mag'] is None: data['v_mag'] = get_val('V')
        if data['i_mag'] is None: data['i_mag'] = get_val('I')
        if data['j_mag'] is None: data['j_mag'] = get_val('J')
        if data['k_mag'] is None: data['k_mag'] = get_val('K')

        return data

    except Exception as e:
        # print(f"Simbad error: {e}")
        return None


def download_lightcurve(ra, dec):
    """
    Скачивание данных.
    ВАЖНО: Radius увеличен до 20 arcsec, чтобы попадать в пиксели TESS.
    """
    try:
        coords = SkyCoord(ra, dec, unit=(u.deg, u.deg))

        # УВЕЛИЧИЛИ РАДИУС ДО 20 секунд (было 1-2)
        search = lk.search_lightcurve(coords, radius=20 * u.arcsec)

        if len(search) == 0:
            return None

        # Фильтруем: берем только данные >= 60c (Long Cadence), чтобы не качать гигабайты
        search = search[search.exptime.value >= 60]

        if len(search) == 0:
            return None

        # Логика выбора лучшего файла:
        # 1. Предпочитаем Kepler (данные чище)
        # 2. Иначе берем TESS
        best_idx = 0
        for i, mission in enumerate(search.mission):
            if 'Kepler' in str(mission) or 'K2' in str(mission):
                best_idx = i
                break

        # Скачиваем ТОЛЬКО ОДИН файл
        lc = search[best_idx].download()

        return lc

    except Exception:
        return None