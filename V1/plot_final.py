import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_map():
    df = pd.read_csv("universal_map_large.csv")
    df = df[df['Gaia_Dist'] > 0]

    plt.figure(figsize=(10, 7))
    plt.scatter(df['Gaia_Dist'], df['Calc_Dist'], c=df['Dust_Av'], cmap='coolwarm', alpha=0.6)
    plt.plot([0, df['Gaia_Dist'].max()], [0, df['Gaia_Dist'].max()], 'k--')
    plt.colorbar(label='Dust Absorption (Av)')
    plt.xlabel('Gaia Distance (pc)')
    plt.ylabel('Calculated Distance (pc)')
    plt.title('Dust Diagnostic Map (5000+ Stars)')
    plt.savefig("final_analysis.png")
    plt.show()


if __name__ == "__main__": plot_map()