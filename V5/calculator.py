import numpy as np


def calculate_distances(df):
    print("Расчет абсолютных величин по типам звезд...")

    def get_m_abs(row):
        p = row['period']
        st = str(row['sub_type']).upper()

        # 1. Классические Цефеиды (DCEP)
        if 'DCEP' in st:
            return -2.76 * np.log10(p) - 1.45

        # 2. Цефеиды II типа (W Vir, BL Her)
        elif 'T2CEP' in st or 'CW' in st:
            return -1.64 * np.log10(p) - 0.65

        # 3. RR Лиры (считаем в среднем для RRAB/RRC)
        elif 'RR' in st:
            return -1.87 * np.log10(p) - 0.64

        return np.nan

    # Применяем формулы
    df['M_calc'] = df.apply(get_m_abs, axis=1)

    # Удаляем если тип не распознан
    df = df.dropna(subset=['M_calc']).copy()

    # Расстояние по закону Ливитта (фотометрическое)
    df['dist_pl'] = 10 ** ((df['v_mag'] - df['M_calc'] + 5) / 5)

    # Расстояние по параллаксу Gaia (эталонное)
    df['dist_ref'] = 1000 / df['parallax']

    # Твоя "Карта поглощения" — относительная ошибка
    df['rel_error'] = (df['dist_pl'] - df['dist_ref']) / df['dist_ref'] * 100

    return df