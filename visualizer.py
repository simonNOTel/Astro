import matplotlib.pyplot as plt
import os

if not os.path.exists("plots"): os.makedirs("plots")

def save_plots(name, lc, pg, period):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    pg.plot(ax=ax1, title=f"Periodogram: {name}")
    lc.fold(period).scatter(ax=ax2, title=f"Folded P={period:.3f}d")
    plt.tight_layout()
    plt.savefig(f"plots/{name.replace(' ','_')}.png")
    plt.close()