"""Bar chart race -> MP4, multi-formats (vertical / carré / horizontal).

Usage:
    python bar_race.py                       # data/sample.csv, tous les formats
    python bar_race.py data/mes_data.csv --formats vertical --title "Mon titre"

CSV attendu (format large) : 1ere colonne = temps (année, date...), 1 colonne par entité.
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FFMpegWriter, FuncAnimation

FORMATS = {  # (largeur, hauteur) en pixels
    "vertical": (1080, 1920),
    "carre": (1080, 1080),
    "horizontal": (1920, 1080),
}
BRAND_DIR = Path(__file__).resolve().parent.parent / "branding"
BRAND = json.loads((BRAND_DIR / "brand.json").read_text(encoding="utf-8"))
BG, FG, MUTED = BRAND["colors"]["bg"], BRAND["colors"]["fg"], BRAND["colors"]["muted"]
ACCENT = BRAND["colors"]["accent"]
PALETTE = BRAND["colors"]["palette"]
LOGO_MARK = plt.imread(BRAND_DIR / "assets" / "logo_mark.png")
LOGO_FULL = plt.imread(BRAND_DIR / "assets" / "logo_full.png")
OUTRO_SECONDS, HOLD_SECONDS = 2.5, 1.0


def load(path):
    df = pd.read_csv(path, index_col=0)
    return df.astype(float)


def interpolate(df, steps):
    """Insère `steps` images entre chaque période (interpolation linéaire)."""
    x_old = np.arange(len(df))
    x_new = np.linspace(0, len(df) - 1, (len(df) - 1) * steps + 1)
    data = np.column_stack([np.interp(x_new, x_old, df[c]) for c in df.columns])
    labels = [df.index[min(int(round(i)), len(df) - 1)] for i in x_new]
    return pd.DataFrame(data, columns=df.columns), labels


def smooth_ranks(values, prev_ranks, order, cap, speed=0.5, margin=0.02):
    """Rang décimal qui glisse vers le rang cible -> transitions fluides.

    Le rang est plafonné à `cap` : un nom hors classement attend juste sous le bas
    de l'écran au lieu de traverser tout le classement (évite chevauchements).
    """
    # Hystérésis : deux barres ne permutent que si l'écart dépasse `margin` (évite le
    # va-et-vient et les superpositions quand deux valeurs sont quasi égales).
    order = list(order)
    changed = True
    while changed:
        changed = False
        for k in range(len(order) - 1):
            a, b = order[k], order[k + 1]
            if values[b] > values[a] * (1 + margin):
                order[k], order[k + 1] = b, a
                changed = True
    target = np.empty(len(values))
    target[order] = np.arange(len(values))
    target = np.minimum(target, cap)
    return prev_ranks + (target - prev_ranks) * speed, order


def render(df, out, fmt, title, subtitle, fps, steps, top_n, unit):
    w, h = FORMATS[fmt]
    dpi = 100
    vertical = h > w
    data, labels = interpolate(df, steps)
    colors = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(df.columns)}
    n = min(top_n, len(df.columns))
    vmax = df.values.max() * 1.15

    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0.30 if vertical else 0.22, 0.08, 0.64, 0.72])
    ax.set_facecolor(BG)
    fs = 26 if vertical else 20

    # Éléments de la vue "graphique"
    chart_items = [
        fig.text(0.06, 0.93, title, color=FG, fontsize=fs * 1.5, fontweight="bold", va="top"),
        fig.text(0.06, 0.875 if vertical else 0.865, subtitle, color=MUTED, fontsize=fs * 0.8, va="top"),
        fig.text(0.06, 0.04, BRAND["handle"], color=ACCENT, fontsize=fs * 0.9,
                 fontweight="bold", ha="left", va="bottom"),
    ]
    clock = fig.text(0.94, 0.04, "", color=MUTED, fontsize=fs * 2.4, fontweight="bold",
                     ha="right", va="bottom", alpha=0.9)
    chart_items.append(clock)
    lh = 0.055 if vertical else 0.09          # hauteur du logo (fraction de la figure)
    lw_ = lh * h / w
    logo_ax = fig.add_axes([0.94 - lw_, 0.93 - lh, lw_, lh])
    logo_ax.imshow(LOGO_MARK); logo_ax.axis("off")
    chart_items.append(logo_ax)

    # Éléments de l'écran de fin
    ow = 0.78 if vertical else 0.42
    oh = ow * (LOGO_FULL.shape[0] / LOGO_FULL.shape[1]) * w / h
    outro_logo = fig.add_axes([0.5 - ow / 2, 0.56 - oh / 2, ow, oh])
    outro_logo.imshow(LOGO_FULL); outro_logo.axis("off")
    outro_items = [
        outro_logo,
        fig.text(0.5, 0.56 - oh / 2 - 0.03, BRAND["tagline"], color=MUTED, fontsize=fs,
                 ha="center", va="top"),
        fig.text(0.5, 0.25, BRAND["cta"], color=FG, fontsize=fs * 1.1, fontweight="bold",
                 ha="center", va="center"),
        fig.text(0.5, 0.20, BRAND["handle"], color=ACCENT, fontsize=fs * 1.3, fontweight="bold",
                 ha="center", va="center"),
    ]
    for it in outro_items:
        it.set_visible(False)
    hold, outro = int(HOLD_SECONDS * fps), int(OUTRO_SECONDS * fps)
    n_main = len(data)

    ranks = np.minimum((-data.iloc[0].values).argsort().argsort().astype(float), n)
    state = {"ranks": ranks, "order": list(np.argsort(-data.iloc[0].values, kind="stable"))}

    def draw(i):
        ax.clear()
        ax.set_facecolor(BG)
        in_outro = i >= n_main + hold
        for it in chart_items:
            it.set_visible(not in_outro)
        for it in outro_items:
            it.set_visible(in_outro)
        if in_outro:
            ax.axis("off")
            return
        i = min(i, n_main - 1)
        vals = data.iloc[i].values
        state["ranks"], state["order"] = smooth_ranks(
            vals, state["ranks"], state["order"], cap=n)
        r = state["ranks"]
        # Axe dynamique : suit le max courant (lissé) pour que les barres restent lisibles
        target = vals.max() * 1.18
        state["vmax"] = state["vmax"] + (target - state["vmax"]) * 0.08 if "vmax" in state else target
        vm = state["vmax"]
        for j, name in enumerate(data.columns):
            if r[j] > n - 0.5:
                continue
            y = n - 1 - r[j]
            ax.barh(y, vals[j], height=0.78, color=colors[name])
            ax.text(-vm * 0.015, y, name, ha="right", va="center", color=FG, fontsize=fs, fontweight="bold")
            ax.text(vals[j] + vm * 0.012, y, f"{vals[j]:,.0f}{unit}".replace(",", " "),
                    ha="left", va="center", color=MUTED, fontsize=fs * 0.9)
        ax.set_xlim(0, vm)
        ax.set_ylim(-0.7, n - 0.3)
        ax.axis("off")
        clock.set_text(str(labels[i]))

    anim = FuncAnimation(fig, draw, frames=n_main + hold + outro, interval=1000 / fps)
    # Maintien de la dernière image ~1.5 s
    writer = FFMpegWriter(fps=fps, codec="libx264",
                          extra_args=["-pix_fmt", "yuv420p", "-crf", "18"])
    out.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out, writer=writer, dpi=dpi)
    plt.close(fig)
    print(f"OK  {fmt:<10} {w}x{h}  ->  {out}")


def main():
    here = Path(__file__).parent
    p = argparse.ArgumentParser()
    p.add_argument("csv", nargs="?", default=str(here / "data" / "sample.csv"))
    p.add_argument("--formats", nargs="+", default=list(FORMATS), choices=list(FORMATS))
    p.add_argument("--title", default="Titre de la dataviz")
    p.add_argument("--subtitle", default="Source : données d'exemple")
    p.add_argument("--unit", default="")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--steps", type=int, default=30, help="images par période")
    p.add_argument("--top", type=int, default=8)
    a = p.parse_args()

    plt.rcParams["font.family"] = "Segoe UI"
    df = load(a.csv)
    for fmt in a.formats:
        render(df, here / "output" / f"{Path(a.csv).stem}_{fmt}.mp4", fmt,
               a.title, a.subtitle, a.fps, a.steps, a.top, a.unit)


if __name__ == "__main__":
    main()
