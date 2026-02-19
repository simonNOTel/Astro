import pandas as pd

# 1. Загружаем файлы
df_my = pd.read_csv('my_stars_with_distance.csv')
df_map = pd.read_csv('universal_map_large.csv')

# 2. Приводим колонки первого файла к стандарту второго
# Переименовываем: name -> Star, ra -> RA, dec -> Dec
df_my = df_my.rename(columns={
    'name': 'Star',
    'ra': 'RA',
    'dec': 'Dec'
})

# Очищаем имена звезд от случайных пробелов
df_my['Star'] = df_my['Star'].astype(str).str.strip()
df_map['Star'] = df_map['Star'].astype(str).str.strip()

# 3. Объединяем файлы по колонке 'Star'
# how='left' означает, что мы берем все звезды из ВАШЕГО файла
# и ищем для них дополнения в большой карте.
merged = pd.merge(df_my, df_map, on='Star', how='left', suffixes=('', '_old'))

# 4. Обработка дубликатов (Calc_Dist, RA, Dec)
# После слияния могут появиться колонки вроде Calc_Dist_old (из большого файла).
# Мы их удалим, так как ваши новые расчеты актуальнее.
cols_to_drop = [c for c in merged.columns if c.endswith('_old')]
merged = merged.drop(columns=cols_to_drop)

# 5. Собираем финальный порядок колонок
# Выстраиваем их так, чтобы было удобно читать
final_columns = [
    'Star', 'RA', 'Dec', 'sp_type', 'v_mag', 'parallax', 'plx_error',
    'Calc_Dist', 'Calc_Dist_Err', 'Period', 'Method', 'Gaia_Dist', 'Dust_Av', 'Status', 'reliable'
]

# Оставляем только те колонки, которые реально есть в данных
existing_cols = [c for c in final_columns if c in merged.columns]
df_final = merged[existing_cols]

# 6. Сохраняем результат
df_final.to_csv('final_universal_map.csv', index=False)

print("Ура! Данные успешно объединены.")
print(f"Файл 'final_universal_map.csv' готов. Найдено совпадений: {merged['Method'].notna().sum()}")