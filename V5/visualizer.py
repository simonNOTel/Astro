import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u


def plot_by_type(df):
    print("Подготовка карты погрешностей...")

    # Перевод в галактические координаты
    coords = SkyCoord(ra=df['ra'].values * u.deg,
                      dec=df['dec'].values * u.deg,
                      frame='icrs').galactic

    l_raw = coords.l.wrap_at(180 * u.deg).degree
    b_raw = coords.b.degree

    plt.figure(figsize=(14, 7))

    # Рисуем карту, где цвет — это ошибка (твое поглощение)
    scatter = plt.scatter(l_raw, b_raw,
                          c=df['rel_error'],
                          cmap='coolwarm',
                          s=10, alpha=0.6,
                          vmin=-50, vmax=150)

    plt.colorbar(scatter, label='Погрешность (Сигнал поглощения) %')
    plt.axhline(0, color='black', lw=1, ls='--')  # Экватор Галактики

    plt.title('Галактическая карта поглощения и аномалий')
    plt.xlabel('Долгота l')
    plt.ylabel('Широта b')
    plt.xlim(180, -180)
    plt.grid(True, alpha=0.3)

    plt.show()