from data_fetcher import fetch_gaia_data
from calculator import calculate_distances
from visualizer import plot_by_type

if __name__ == "__main__":
    # 1. Загрузка
    raw_data = fetch_gaia_data()

    # ПРОВЕРКА: если данных нет, выходим
    if raw_data.empty:
        print("!!! Работа остановлена: данные не были получены от сервера Gaia.")
        print("Пожалуйста, проверьте интернет или подождите, пока сервер ESA возобновит работу.")
    else:
        # 2. Расчет
        processed_data = calculate_distances(raw_data)

        # 3. Результат
        print(f"Средняя ошибка по всей выборке: {processed_data['rel_error'].mean():.2f}%")
        processed_data.to_csv("improved_stars_data.csv", index=False)

        # 4. Визуализация
        plot_by_type(processed_data)