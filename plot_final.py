import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Загружаем результаты
df = pd.read_csv("universal_map.csv")

# Фильтруем пустые значения
df = df.dropna(subset=['Gaia_Dist', 'Calc_Dist'])

plt.figure(figsize=(10, 8))

# 1. Линия идеального совпадения (y = x)
max_val = max(df['Gaia_Dist'].max(), df['Calc_Dist'].max())
plt.plot([0, max_val], [0, max_val], 'k--', label='Идеальное совпадение (Clean Space)')

# 2. Зоны аномалий
x = np.linspace(0, max_val, 100)
plt.fill_between(x, x, x * 1.5, color='red', alpha=0.1, label='Зона Пыли (Av > 0)')
plt.fill_between(x, x * 0.5, x, color='blue', alpha=0.1, label='Зона Двойных/Обертонов (Av < 0)')

# 3. Точки звезд
# Разделяем по типам для красоты
cepheids = df[df['Type'].str.contains('Cepheid')]
rr_lyrae = df[df['Type'].str.contains('RR_Lyrae')]

plt.scatter(cepheids['Gaia_Dist'], cepheids['Calc_Dist'],
            c='red', s=100, marker='*', label='Цефеиды')

plt.scatter(rr_lyrae['Gaia_Dist'], rr_lyrae['Calc_Dist'],
            c='blue', s=80, marker='o', label='RR Лиры')

# Подписи названий звезд
for i, row in df.iterrows():
    plt.text(row['Gaia_Dist'], row['Calc_Dist'], row['Star'], fontsize=9)

plt.xlabel("Расстояние по Gaia (пк) [Эталон]", fontsize=12)
plt.ylabel("Расстояние по нашему коду (пк) [Фотометрия]", fontsize=12)
plt.title("Диагностическая карта межзвездной среды и аномалий", fontsize=14)
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)

plt.savefig("final_map.png", dpi=300)
plt.show()