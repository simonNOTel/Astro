import pandas as pd
import numpy as np
import plotly.graph_objects as go
from astropy.coordinates import SkyCoord
import astropy.units as u
import os


def create_3d_star_map(input_file):
    if not os.path.exists(input_file):
        print(f"❌ Файл {input_file} не найден!")
        return

    df = pd.read_csv(input_file)

    # 1. СТРОГИЙ ФИЛЬТР (как в 2D)
    # Оставляем только те звезды, где расчеты имеют смысл
    # Убираем относительную ошибку более 200% и менее -100%
    df = df[(df['rel_error'] > -100) & (df['rel_error'] < 200)]

    # Ограничиваем расстояние до 10 000 пк, чтобы не было "разлета" карты
    df = df[df['dist_ref'] < 10000]

    print(f"Число звезд после фильтрации: {len(df)}")

    # Координаты
    coords = SkyCoord(ra=df['ra'].values * u.degree,
                      dec=df['dec'].values * u.degree,
                      distance=df['dist_ref'].values * u.pc,
                      frame='icrs')
    galactic = coords.galactic
    df['x'], df['y'], df['z'] = galactic.cartesian.x.value, galactic.cartesian.y.value, galactic.cartesian.z.value

    fig = go.Figure()

    # Основные точки
    fig.add_trace(go.Scatter3d(
        x=df['x'], y=df['y'], z=df['z'],
        mode='markers',
        marker=dict(
            size=3,
            color=df['rel_error'],
            colorscale='Jet',
            # ЖЕСТКАЯ ПРИВЯЗКА ШКАЛЫ (как в 2D vmin/vmax)
            cmin=-50,
            cmax=150,
            showscale=True,
            colorbar=dict(title="Ошибка %", thickness=20),
            opacity=1  # Делаем точки плотными
        ),
        text=df['name'],
        hovertemplate="ID: %{text}<br>Ошибка: %{marker.color:.1f}%<extra></extra>"
    ))

    # Солнце
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(size=8, color='white', symbol='diamond'),
        name='Солнце'
    ))

    fig.update_layout(
        title="Финальная 3D модель зон экстинкции",
        scene=dict(
            xaxis=dict(title='X (pc)', backgroundcolor="black", gridcolor="gray"),
            yaxis=dict(title='Y (pc)', backgroundcolor="black", gridcolor="gray"),
            zaxis=dict(title='Z (pc)', backgroundcolor="black", gridcolor="gray"),
            aspectmode='cube'  # Чтобы визуально не сплющивало Галактику
        ),
        paper_bgcolor='black',
        font=dict(color='white')
    )

    fig.write_html("stellar_3d_final.html")
    fig.show()


if __name__ == "__main__":
    create_3d_star_map('stars_calculated.csv')