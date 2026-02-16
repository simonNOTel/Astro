import matplotlib.pyplot as plt
import os

# Создаем папку для графиков, если нет
if not os.path.exists("plots"):
    os.makedirs("plots")


def save_plots(star_name, lc, pg, period):
    """Строит и сохраняет фазовую кривую и периодограмму."""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 1. Периодограмма
    pg.plot(ax=ax1, title=f"Periodogram: {star_name}")
    ax1.text(0.5, 0.9, f"P = {period:.3f} d", transform=ax1.transAxes,
             fontsize=12, color='red', ha='center')

    # 2. Фазовая кривая (свернутая с найденным периодом)
    lc.fold(period).scatter(ax=ax2, label=f"Folded P={period:.2f}d")
    ax2.set_title(f"Phased Light Curve: {star_name}")

    plt.tight_layout()
    filename = f"plots/{star_name}_analysis.png"
    plt.savefig(filename)
    plt.close()  # Закрываем, чтобы не жрать память
    return filename