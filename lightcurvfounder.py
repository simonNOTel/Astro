import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import lightkurve as lk
from astropy.timeseries import LombScargle
import warnings

warnings.filterwarnings('ignore')


# ==========================================
# ШАГ 1: ЗАГРУЗКА ДАННЫХ
# ==========================================
def load_data(filepath):
    print("Загрузка базы данных...")
    df = pd.read_csv(filepath)
    # Очистка от строк с отсутствующим эталонным параллаксом
    df = df.dropna(subset=['gaia_parallax', 'RA', 'Dec', 'Calc_Dist']).reset_index(drop=True)
    print(f"Загружено {len(df)} звезд для анализа.")
    return df


# ==========================================
# ШАГ 2: ПОИСК ЦИФРОВОГО СЛЕДА И ПЕРИОДА (ЛОМБ-СКАРГЛ)
# ==========================================
def download_and_find_period(star_name, ra, dec):
    """
    Ищет кривую блеска звезды в архивах TESS/Kepler по координатам или имени,
    скачивает ее и находит период методом Ломба-Скаргла.
    """
    print(f"Поиск данных для {star_name}...")
    try:
        # Ищем кривые блеска (короткая экспозиция TESS как пример)
        search_result = lk.search_lightcurve(f"{ra} {dec}", radius=0.001, author='SPOC', exptime=120)

        if len(search_result) == 0:
            return None, "Данные не найдены"

        # Скачиваем первую найденную кривую и убираем NaN
        lc = search_result[0].download().remove_nans().normalize()

        # Анализ периодичности: Метод Ломба-Скаргла
        # Переводим во внутренний формат Astropy
        time = lc.time.value
        flux = lc.flux.value

        # Строим периодограмму
        ls = LombScargle(time, flux)
        frequency, power = ls.autopower(minimum_frequency=0.01, maximum_frequency=10.0)

        # Находим период с максимальной мощностью
        best_freq = frequency[np.argmax(power)]
        period = 1 / best_freq

        return period, "Успешно"
    except Exception as e:
        return None, str(e)


# ==========================================
# ШАГ 3 & 4: ДИАГНОСТИКА СРЕДЫ И ПОИСК АНОМАЛИЙ
# ==========================================
def analyze_diagnostics(df):
    """
    Сравнивает D_calc (по фотометрии) и D_gaia (по геометрии).
    Ищет аномалии (например, неразрешенные двойные системы).
    """
    print("Проведение диагностики среды и поиск аномалий...")

    # 1. Убедимся, что D_gaia рассчитано корректно (1000 / parallax в mas)
    # Если параллакс отрицательный или нулевой (ошибки измерений), игнорируем
    valid_gaia = df['gaia_parallax'] > 0
    df.loc[valid_gaia, 'D_Gaia_Check'] = 1000 / df.loc[valid_gaia, 'gaia_parallax']

    # 2. Выявление аномалий (Слишком малое расчетное расстояние)
    # Если D_calc сильно меньше D_Gaia (например, на 30% и более),
    # звезда кажется ярче, чем должна быть -> возможная двойная система
    anomaly_threshold = 0.7
    df['Is_Anomaly'] = (df['Calc_Dist'] < (anomaly_threshold * df['Gaia_Dist_Calc']))

    anomalies = df[df['Is_Anomaly']]
    print(f"Обнаружено {len(anomalies)} аномальных объектов (кандидаты в двойные системы или ошибки).")

    # 3. Диагностика пыли: Если D_calc (без учета Везенайта) > D_Gaia -> свет поглощается
    # Предполагается, что индекс 'Dust_Av' в вашем датасете уже содержит эту оценку,
    # но мы можем добавить флаг сильного поглощения
    df['High_Extinction'] = df['Dust_Av'] > 1.0  # Условный порог Av > 1 зв. вел.

    return df, anomalies


# ==========================================
# ШАГ 5: ПОСТРОЕНИЕ 3D КАРТЫ РАСПРЕДЕЛЕНИЯ ПЫЛИ
# ==========================================
def plot_3d_dust_map(df):
    """
    Переводит координаты (RA, Dec, Расстояние) в декартовы (X, Y, Z)
    и строит 3D-карту распределения межзвездной пыли в окрестностях Солнца.
    """
    print("Генерация 3D-карты Галактики...")

    # Отбрасываем экстремальные выбросы для красивой визуализации (например, дистанция > 10000 пк)
    plot_df = df[df['Gaia_Dist_Calc'] < 10000].copy()

    # Перевод RA и Dec из градусов в радианы
    ra_rad = np.radians(plot_df['RA'])
    dec_rad = np.radians(plot_df['Dec'])
    d = plot_df['Gaia_Dist_Calc']

    # Перевод сферических координат в декартовы (с центром в Солнечной системе, X, Y, Z в парсеках)
    plot_df['X'] = d * np.cos(dec_rad) * np.cos(ra_rad)
    plot_df['Y'] = d * np.cos(dec_rad) * np.sin(ra_rad)
    plot_df['Z'] = d * np.sin(dec_rad)

    # Построение
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Точки: цвет зависит от плотности пыли (Dust_Av)
    # Используем colormap (от желтого к темно-красному/черному)
    sc = ax.scatter(plot_df['X'], plot_df['Y'], plot_df['Z'],
                    c=plot_df['Dust_Av'], cmap='inferno_r',
                    s=15, alpha=0.8, edgecolors='none')

    # Добавляем Солнце в центр (0, 0, 0)
    ax.scatter([0], [0], [0], color='blue', marker='*', s=200, label='Солнце')

    cb = plt.colorbar(sc, shrink=0.5, pad=0.1)
    cb.set_label('Межзвездное поглощение (Dust $A_v$)', fontsize=12)

    ax.set_xlabel('X (Парсеки)')
    ax.set_ylabel('Y (Парсеки)')
    ax.set_zlabel('Z (Парсеки)')
    ax.set_title('3D-карта распределения пыли в окрестностях Солнца', fontsize=15)
    ax.legend()

    # Сохраняем и показываем
    plt.savefig('galaxy_dust_3d_map.png', dpi=300)
    print("Карта сохранена как 'galaxy_dust_3d_map.png'.")
    plt.show()


# ==========================================
# ГЛАВНЫЙ ИСПОЛНИТЕЛЬНЫЙ БЛОК
# ==========================================
if __name__ == "__main__":
    filepath = "candidates_list.csv"

    try:
        # 1. Загрузка
        df = load_data(filepath)

        # 2. Массовая диагностика и поиск аномалий
        df, anomalies = analyze_diagnostics(df)

        # Сохраним аномалии в отдельный файл
        if not anomalies.empty:
            anomalies.to_csv('anomalies_found.csv', index=False)
            print("Список аномальных звезд сохранен в 'anomalies_found.csv'.")

        # 3. Визуализация 3D-карты пыли
        plot_3d_dust_map(df)

        # 4. Демонстрация скачивания кривой блеска для первой аномальной звезды (Опционально)
        if not anomalies.empty:
            test_star = anomalies.iloc[0]
            print(f"\nТестируем скачивание кривой блеска для аномалии: {test_star['Star']}")
            period, status = download_and_find_period(test_star['Star'], test_star['RA'], test_star['Dec'])
            if period:
                print(f"Рассчитанный период (Ломб-Скаргл): {period:.4f} дней")
                print(f"Период в вашей базе (Period): {test_star['Period']} дней")
            else:
                print(f"Не удалось рассчитать период: {status}")

    except FileNotFoundError:
        print(f"Файл {filepath} не найден. Убедитесь, что он лежит в той же папке, что и скрипт.")v