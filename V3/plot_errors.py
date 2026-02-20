import pandas as pd
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u


def plot_error_map(input_file):
    print(f"Загружаем данные из {input_file}...")
    df = pd.read_csv(input_file)

    # 1. Отсекаем дикие выбросы (ошибки > 300%), чтобы они не портили шкалу
    df_filtered = df[df['rel_error'].abs() < 300].copy()
    print(f"Звезд для графика (после отсева аномалий): {len(df_filtered)}")

    # 2. Переводим RA и Dec в Галактические координаты (l, b)
    print("Конвертируем координаты в галактическую систему...")

    # ИСПРАВЛЕНИЕ ЗДЕСЬ: вытаскиваем чистые numpy-массивы через .values
    ra_vals = df_filtered['ra'].astype(float).values
    dec_vals = df_filtered['dec'].astype(float).values

    coords = SkyCoord(ra=ra_vals * u.degree,
                      dec=dec_vals * u.degree,
                      frame='icrs')
    galactic_coords = coords.galactic

    # Добавляем в датафрейм (l - долгота, b - широта)
    l_wrap = galactic_coords.l.wrap_at(180 * u.deg).degree
    df_filtered['gal_l'] = l_wrap
    df_filtered['gal_b'] = galactic_coords.b.degree

    # 3. Настройка графика
    print("Отрисовка карты...")
    plt.figure(figsize=(12, 6))

    # Строим Scatter plot (диаграмму рассеяния)
    scatter = plt.scatter(df_filtered['gal_l'], df_filtered['gal_b'],
                          c=df_filtered['rel_error'],
                          cmap='coolwarm',
                          s=15,  # размер точек
                          alpha=0.8,  # прозрачность
                          vmin=-50, vmax=150)  # ограничиваем шкалу для контраста

    # Оформление осей
    plt.colorbar(scatter, label='Относительная ошибка (%)')
    plt.title('Карта погрешностей расчета расстояний (в Галактических координатах)')
    plt.xlabel('Галактическая долгота $l$ (градусы)')
    plt.ylabel('Галактическая широта $b$ (градусы)')

    # Инвертируем ось X
    plt.xlim(180, -180)
    plt.ylim(-90, 90)

    # Рисуем линию экватора Галактики (там больше всего пыли)
    plt.axhline(0, color='black', linestyle='--', alpha=0.5)

    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # 4. Сохраняем картинку
    plt.savefig('error_map_galactic10000.png', dpi=300)
    print("Карта успешно сохранена в файл 'error_map_galactic.png'!")

    # Показываем окно с графиком
    plt.show()


# Запуск
plot_error_map('stars_calculated.csv')