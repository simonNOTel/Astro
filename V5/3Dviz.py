import pandas as pd
import numpy as np
import plotly.express as px
import os
from astropy.coordinates import SkyCoord
import astropy.units as u
import webbrowser


def create_3d_galaxy_map(file_path):
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл '{file_path}' не найден.")
        return

    print(f"Загрузка данных из {file_path}...")
    # Читаем файл, учитывая возможные пустые значения
    df = pd.read_csv(file_path)

    # 1. Подготовка данных
    # Заменяем пустые значения в дистанциях на NaN для корректной работы
    df['Gaia_Dist'] = pd.to_numeric(df['Gaia_Dist'], errors='coerce')
    df['Calc_Dist'] = pd.to_numeric(df['Calc_Dist'], errors='coerce')

    # Очищаем только совсем битые строки (где нет координат)
    df = df.dropna(subset=['RA', 'Dec'])

    # Используем Gaia_Dist для координат, а если его нет - Calc_Dist
    df['Plot_Dist'] = df['Gaia_Dist'].fillna(df['Calc_Dist']).fillna(0)

    # Оставляем только те звезды, которые хоть где-то имеют дистанцию > 0
    df = df[df['Plot_Dist'] > 0]

    if len(df) == 0:
        print("Ошибка: В файле нет звезд с дистанцией больше 0!")
        return

    # 2. Расчет погрешности (только там, где есть оба значения)
    df['relative_error'] = np.nan
    mask = (df['Gaia_Dist'] > 0) & (df['Calc_Dist'] > 0)
    df.loc[mask, 'relative_error'] = (abs(df['Calc_Dist'] - df['Gaia_Dist']) / df['Gaia_Dist']) * 100

    # 3. Перевод координат в Галактические
    print(f"Конвертирую координаты для {len(df)} звезд...")
    coords = SkyCoord(ra=df['RA'].values * u.degree, dec=df['Dec'].values * u.degree, frame='icrs')
    df['l'] = coords.galactic.l.degree
    df['b'] = coords.galactic.b.degree

    # 4. Декартовы координаты
    l_rad = np.radians(df['l'])
    b_rad = np.radians(df['b'])
    d = df['Plot_Dist']

    df['X'] = d * np.cos(b_rad) * np.cos(l_rad)
    df['Y'] = d * np.cos(b_rad) * np.sin(l_rad)
    df['Z'] = d * np.sin(b_rad)

    # Подготовка шкалы для визуализации
    # Если ошибки нет (Skipped), запишем её как -1, чтобы покрасить в серый
    df['error_viz'] = df['relative_error'].fillna(-1).clip(upper=150)

    # 5. Построение графика
    print("Генерация 3D сцены...")
    fig = px.scatter_3d(
        df,
        x='X', y='Y', z='Z',
        color='error_viz',
        color_continuous_scale=[
            (0, "gray"),  # Ошибки нет или пропущено
            (0.01, "blue"),  # Маленькая ошибка
            (0.5, "yellow"),  # Средняя
            (1.0, "red")  # Большая ошибка (пыль)
        ],
        hover_name='Star',
        hover_data={
            'X': False, 'Y': False, 'Z': False,
            'Gaia_Dist': ':.1f',
            'Calc_Dist': ':.1f',
            'relative_error': ':.2f',
            'Status': True
        },
        title="Интерактивная карта: Погрешности и межзвездная среда",
        range_color=[0, 150]
    )

    fig.update_layout(
        template="plotly_dark",
        scene=dict(
            xaxis_title='X (pc)',
            yaxis_title='Y (pc)',
            zaxis_title='Z (pc)',
            aspectmode='data'
        )
    )

    fig.update_traces(marker=dict(size=2.5, opacity=0.8))

    # 6. Сохранение
    output_file = "Astro_3D_Map_Fixed.html"
    fig.write_html(output_file)
    print(f"Успех! Файл: {os.path.abspath(output_file)}")
    webbrowser.open('file://' + os.path.realpath(output_file))


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    DATA_FILE = os.path.join(script_dir, "results.csv")
    create_3d_galaxy_map(DATA_FILE)