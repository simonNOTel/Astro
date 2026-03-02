import pandas as pd
import numpy as np
import plotly.graph_objects as go
from astropy.coordinates import SkyCoord
import astropy.units as u
import os


def create_3d_star_map(input_file):
    # Проверка наличия файла
    if not os.path.exists(input_file):
        print(f"❌ Файл '{input_file}' не найден в папке {os.getcwd()}")
        return

    print(f"🚀 Читаем данные из {input_file}...")
    df = pd.read_csv(input_file)

    # Чистка данных: убираем строки без координат или расстояния
    df = df.dropna(subset=['ra', 'dec', 'dist_ref', 'rel_error'])

    # Фильтруем экстремальные значения для наглядности (до 15 000 пк)
    df = df[df['dist_ref'] < 15000]

    print(f"Обработка {len(df)} звезд...")

    # 1. Преобразование RA/Dec/Dist -> Галактические X, Y, Z
    # Мы используем dist_ref (точное расстояние по параллаксу Gaia)
    coords = SkyCoord(ra=df['ra'].values * u.degree,
                      dec=df['dec'].values * u.degree,
                      distance=df['dist_ref'].values * u.pc,
                      frame='icrs')

    galactic = coords.galactic
    df['x'] = galactic.cartesian.x.value
    df['y'] = galactic.cartesian.y.value
    df['z'] = galactic.cartesian.z.value

    # 2. Создание визуализации
    fig = go.Figure()

    # Основной массив звезд
    fig.add_trace(go.Scatter3d(
        x=df['x'], y=df['y'], z=df['z'],
        mode='markers',
        marker=dict(
            size=2.5,
            color=df['rel_error'],
            colorscale='RdBu_r',  # Красный = большая ошибка (пыль), Синий = норма
            colorbar=dict(title="Ошибка закона Левитта (%)"),
            cmid=0,
            opacity=0.7
        ),
        text=df['name'],
        hovertemplate=(
                "<b>Звезда: %{text}</b><br>" +
                "Расстояние (Gaia): %{customdata:.1f} pc<br>" +
                "Погрешность: %{marker.color:.1f}%<br>" +
                "<extra></extra>"
        ),
        customdata=df['dist_ref']
    ))

    # Ставим Солнце в центр
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(size=6, color='yellow', symbol='diamond'),
        name='Солнце (Вы здесь)'
    ))

    # Оформление "Космос"
    fig.update_layout(
        title="3D Карта межзвездного поглощения (на основе ошибок Цефеид и RR Лир)",
        scene=dict(
            xaxis=dict(title='X (pc) к центру Галактики', backgroundcolor="black", gridcolor="gray"),
            yaxis=dict(title='Y (pc)', backgroundcolor="black", gridcolor="gray"),
            zaxis=dict(title='Z (pc) перпендикулярно диску', backgroundcolor="black", gridcolor="gray"),
            aspectmode='data'  # Сохраняет пропорции расстояний
        ),
        paper_bgcolor='black',
        font=dict(color='white'),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    output_name = "stellar_3d_error_map.html"
    fig.write_html(output_name)
    print(f"✨ Готово! Открой файл {output_name} в браузере.")
    fig.show()


if __name__ == "__main__":
    create_3d_star_map('stars_calculated.csv')