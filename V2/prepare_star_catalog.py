import pandas as pd


def prepare_star_catalog(input_filename, output_filename):
    # 1. Загружаем исходные данные
    # Предполагаем, что разделитель — запятая
    try:
        df = pd.read_csv(input_filename)
    except FileNotFoundError:
        print(f"Файл {input_filename} не найден.")
        return

    # 2. Выбираем колонки, которые нам точно нужны (Reference data)
    # ra, dec — для карты
    # v_mag — для формулы модуля расстояния
    # Calc_Dist — как эталон (Reference)
    required_columns = [
        'name', 'ra', 'dec', 'sp_type', 'v_mag',
        'parallax', 'Calc_Dist', 'Calc_Dist_Err'
    ]

    # Создаем новый DataFrame только с нужными колонками
    new_df = df[required_columns].copy()

    # 3. Переименовываем Calc_Dist в dist_ref для ясности (эталонное расстояние)
    new_df.rename(columns={'Calc_Dist': 'dist_ref', 'Calc_Dist_Err': 'dist_ref_err'}, inplace=True)

    # 4. Добавляем ПУСТЫЕ колонки для ваших будущих расчетов
    # Период (его нужно будет подтянуть или ввести)
    new_df['period'] = None
    # Рассчитанная вами абсолютная величина
    new_df['M_calc'] = None
    # Рассчитанное вами расстояние по P-L
    new_df['dist_pl'] = None
    # Колонки для погрешностей (будем считать их следующим скриптом)
    new_df['abs_error'] = None
    new_df['rel_error'] = None

    # 5. Сохраняем в новый файл
    new_df.to_csv(output_filename, index=False)
    print(f"Готово! Файл '{output_filename}' создан. Количество звезд: {len(new_df)}")


# Запуск (замените 'your_file.csv' на реальное имя вашего файла)
prepare_star_catalog('my_stars_with_distance.csv', 'stars_prepared.csv')