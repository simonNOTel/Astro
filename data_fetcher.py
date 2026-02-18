import warnings
import numpy as np
import lightkurve as lk
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u

warnings.filterwarnings("ignore")


def get_star_metadata(star_name, ra=None, dec=None):
    """
    Запрашивает V, I, J, K магнитуды и параллакс.
    Поиск по координатам RA/Dec гораздо надежнее поиска по имени.
    """
    Simbad.reset_votable_fields()
    Simbad.add_votable_fields('flux(V)', 'flux(I)', 'flux(J)', 'flux(K)', 'plx')

    try:
        table = None
        if ra is not None and dec is not None:
            coords = SkyCoord(ra, dec, unit=(u.deg, u.deg))
            table = Simbad.query_region(coords, radius=5 * u.arcsec)

        if table is None:
            table = Simbad.query_object(star_name)

        if table is None: return None

        row = table[0]

        def get_val(col_name):
            for key in [col_name, f'FLUX_{col_name}', col_name.upper()]:
                if key in table.colnames and not np.ma.is_masked(row[key]):
                    return float(row[key])
            return None

        return {
            "v_mag": get_val('V'),
            "i_mag": get_val('I'),
            "j_mag": get_val('J'),
            "k_mag": get_val('K'),
            "parallax_mas": get_val('PLX_VALUE') or get_val('PLX')
        }
    except:
        return None


def download_lightcurve(ra, dec):
    """
    Скачивает кривую блеска по координатам.
    Радиус 20 arcsec оптимален для TESS.
    """
    try:
        coords = SkyCoord(ra, dec, unit=(u.deg, u.deg))
        search = lk.search_lightcurve(coords, radius=20 * u.arcsec)

        if len(search) == 0: return None

        # Фильтруем длинные экспозиции (>= 60s), чтобы избежать тяжелых данных
        search = search[search.exptime.value >= 60]
        if len(search) == 0: return None

        # Приоритет Kepler над TESS
        best_idx = 0
        for i, mission in enumerate(search.mission):
            if 'Kepler' in str(mission):
                best_idx = i
                break

        return search[best_idx].download()
    except:
        return None