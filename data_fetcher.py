import lightkurve as lk

def download_lightcurve(name):
    try:
        search = lk.search_lightcurve(name, author='SPOC')
        if not search: search = lk.search_lightcurve(name, mission='Kepler')
        return search[0].download() if search else None
    except: return None