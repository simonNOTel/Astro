import pandas as pd
import numpy as np


def calculate_absolute_magnitude(period, star_type):
    # Защита от пустых значений или нулей
    if pd.isna(period) or period <= 0:
        return np.nan

    # Приводим тип к строке и верхнему регистру для удобства поиска
    stype = str(star_type).upper()

    # Классические Цефеиды (DCEP, CEP)
    if 'CEP' in stype or 'DCEP' in stype:
        return -2.76 * np.log10(period) - 1.45

    # RR Лиры (RR, RRAB, RRC)
    elif 'RR' in stype:
        return -1.87 * np.log10(period) - 0.64

    # Углеродные звезды (C, C-N) и Долгопериодические (M, SR, L) - УПРОЩЕННО
    elif 'C-' in stype or 'SR' in stype or 'M' in stype:
        # Для них в V-диапазоне закон работает хуже, это грубая оценка
        return -2.0 * np.log10(period) + 1.0

        # Для всех остальных типов возвращаем NaN (не считаем)
    else:
        return np.nan


def process_calculations(input_file, output_file):
    print(f"1. Загружаем данные из {input_file}...")
    df = pd.read_csv(input_file)

    # Отбрасываем звезды, для которых мы не нашли период или у которых нет видимой величины (v_mag)
    initial_count = len(df)
    df = df.dropna(subset=['period', 'v_mag', 'dist_ref'])
    print(f"После удаления строк без периодов и базовых данных осталось: {len(df)} из {initial_count} звезд.")

    # 2. Считаем абсолютную величину (M)
    print("2. Вычисляем абсолютную звездную величину (M_calc)...")
    df['M_calc'] = df.apply(lambda row: calculate_absolute_magnitude(row['period'], row['sp_type']), axis=1)

    # Убираем те, которые не подошли по типу (где M_calc = NaN)
    df = df.dropna(subset=['M_calc'])
    print(f"Звезд подходящих типов (Цефеиды, RR Лиры, C-типы) для расчетов: {len(df)}")

    # 3. Считаем наше фотометрическое расстояние (dist_pl) в парсеках
    print("3. Вычисляем фотометрическое расстояние по закону Левитта...")
    df['dist_pl'] = 10 ** ((df['v_mag'] - df['M_calc'] + 5) / 5)

    # 4. Считаем погрешности
    print("4. Вычисляем погрешности...")
    # Абсолютная ошибка: Насколько парсек мы ошиблись
    df['abs_error'] = df['dist_pl'] - df['dist_ref']

    # Относительная ошибка: Процент ошибки от эталонного расстояния
    df['rel_error'] = (df['abs_error'] / df['dist_ref']) * 100

    # Округляем для красоты
    df['M_calc'] = df['M_calc'].round(3)
    df['dist_pl'] = df['dist_pl'].round(2)
    df['abs_error'] = df['abs_error'].round(2)
    df['rel_error'] = df['rel_error'].round(2)

    # 5. Сохраняем результат
    df.to_csv(output_file, index=False)
    print(f"5. Успех! Итоговые данные сохранены в '{output_file}'.")

    # Выводим среднюю ошибку для понимания масштаба трагедии (или успеха)
    mean_error = df['rel_error'].abs().mean()
    print(f"Средняя относительная ошибка по всей выборке: {mean_error:.2f}%")


# Запуск
process_calculations('stars_with_periods.csv', 'stars_calculated.csv')