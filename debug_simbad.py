import pyvo as vo
import pandas as pd


def debug_simbad_standards():
    service = vo.dal.TAPService("http://simbad.u-strasbg.fr/simbad/sim-tap")

    print("--- ШАГ 1: Сканирование эталона (Delta Cephei) ---")
    # Дельта Цефея: RA=337.28, DEC=+58.41
    # Мы ищем все объекты в радиусе 0.1 градуса от этой точки
    # и просим показать их типы и фильтры яркости.

    query = """
    SELECT TOP 10
        basic.main_id, 
        basic.otype, 
        flux.filter, 
        flux.flux
    FROM basic
    JOIN flux ON basic.oid = flux.oidref
    WHERE 
        1=CONTAINS(POINT('ICRS', basic.ra, basic.dec), CIRCLE('ICRS', 337.28, 58.41, 0.05))
    """

    try:
        result = service.search(query)
        df = result.to_table().to_pandas()

        if len(df) > 0:
            print("УСПЕХ! Данные получены. Вот как они выглядят в базе:")
            print(df)
            print("\n>>> ВАЖНО: Скопируйте точное значение из колонки 'otype' и 'filter' ниже:")
            print(f"Типы (otype): {df['otype'].unique()}")
            print(f"Фильтры (filter): {df['filter'].unique()}")
        else:
            print("Ошибка: Даже по координатам ничего не найдено. Возможно, проблема с сетью или сервером SIMBAD.")

    except Exception as e:
        print(f"Ошибка запроса: {e}")
        if hasattr(e, 'content'):
            print(f"Детали: {e.content}")


if __name__ == "__main__":
    debug_simbad_standards()