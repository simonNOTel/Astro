import lightkurve as lk
from astropy.coordinates import SkyCoord
import astropy.units as u


def download_lightcurve(ra, dec, radius_arcsec=10):
    """Скачивание данных TESS/Kepler по координатам."""
    try:
        # Создаем объект координат
        coord = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

        # 1. Сначала ищем в TESS (он покрывает больше ваших звезд)
        # Убираем жесткую привязку к автору 'SPOC', чтобы найти данные QLP (из FFI)
        search = lk.search_lightcurve(coord, radius=radius_arcsec, mission='TESS')

        if len(search) == 0:
            # 2. Если в TESS нет, пробуем Kepler
            search = lk.search_lightcurve(coord, radius=radius_arcsec, mission='Kepler')

        if len(search) == 0:
            return None

        # Берем самый длинный кусок данных (обычно там меньше шума)
        best_lc = search[0].download()
        return best_lc
    except Exception as e:
        # print(f"Ошибка загрузки: {e}")
        return None