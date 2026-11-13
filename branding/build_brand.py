"""Génère le logo (marque seule + version complète) depuis brand.json.

Marque : une fleur dont les pétales ont des longueurs différentes (clin d'oeil radar/bar chart).
Sorties dans branding/assets : logo_mark.png/.svg, logo_full.png
Usage : python build_brand.py
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch

HERE = Path(__file__).parent
B = json.loads((HERE / "brand.json").read_text(encoding="utf-8"))
C = B["colors"]
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
plt.rcParams["font.family"] = B["font"]

# Longueurs relatives des 6 pétales (données !) -- angle de départ en haut
PETALS = [0.34, 0.26, 0.38, 0.24, 0.32, 0.28]
SPLIT = 4  # "Data" | "blossom" : 2 couleurs dans le nom


def draw_mark(ax, x0=0.0, y0=0.0, s=1.0):
    ax.add_patch(FancyBboxPatch((x0, y0), s, s, boxstyle=f"round,pad=0,rounding_size={0.22*s}",
                                fc=C["accent"], ec="none"))
    cx, cy = x0 + s / 2, y0 + s / 2
    n = len(PETALS)
    for k, L in enumerate(PETALS):
        theta = math.pi / 2 + 2 * math.pi * k / n
        length = L * s
        px = cx + math.cos(theta) * (length / 2 + 0.03 * s)
        py = cy + math.sin(theta) * (length / 2 + 0.03 * s)
        ax.add_patch(Ellipse((px, py), length, 0.17 * s, angle=math.degrees(theta),
                             fc=C["bg"], ec="none"))
    ax.add_patch(Ellipse((cx, cy), 0.13 * s, 0.13 * s, fc=C["accent"], ec=C["bg"], lw=0))
    ax.add_patch(Ellipse((cx, cy), 0.075 * s, 0.075 * s, fc=C["bg"], ec="none"))


def save_mark():
    fig = plt.figure(figsize=(4, 4), dpi=256)
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.92])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
    draw_mark(ax)
    fig.savefig(OUT / "logo_mark.png", transparent=True)
    fig.savefig(OUT / "logo_mark.svg", transparent=True)
    plt.close(fig)


def save_full():
    name = B["name"]
    fig = plt.figure(figsize=(12, 2.6), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 12); ax.set_ylim(0, 2.6); ax.axis("off")
    draw_mark(ax, 0.3, 0.3, 2.0)
    t1 = ax.text(2.8, 1.3, name[:SPLIT], color=C["fg"], fontsize=62,
                 fontweight="bold", va="center", ha="left")
    fig.canvas.draw()
    bb = t1.get_window_extent().transformed(ax.transData.inverted())
    t2 = ax.text(bb.x1, 1.3, name[SPLIT:], color=C["accent"], fontsize=62,
                 fontweight="bold", va="center", ha="left")
    fig.canvas.draw()
    end = t2.get_window_extent().transformed(ax.transData.inverted()).x1
    ax.set_xlim(0, end + 0.3)  # recadre à droite
    fig.set_size_inches((end + 0.3), 2.6)
    fig.savefig(OUT / "logo_full.png", transparent=True)
    plt.close(fig)


if __name__ == "__main__":
    save_mark()
    save_full()
    print("OK ->", OUT)
