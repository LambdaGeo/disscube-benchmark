"""Figure: four DisSCube operators against the TerraME Fill goldens, same cells, same colour scale.

    ./run.sh all itaituba
    ./run.sh all majority
    python figure_operators.py --out reports/operators/fig_operators.png

Top row: DisSCube. Bottom row: TerraME (the golden of luccme-goldens, read as compare.py reads it,
with the same SHA-256 check). One column per operator, on the Itaituba grid (31 x 20 cells of 5 km):

    mean        elevation   (m)
    percentage  defor_87    (share of the cell covered by class 87)
    distance    distroad    (km, to the nearest road)
    majority    defor_mode  (predominant deforestation class)

Both rows use the same cells and the same limits, so a difference in the picture is a difference
in the values. The largest absolute difference of each column is printed under it.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tomllib
from compare import _cells, _load_reference
from disscube import CubeClient
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent

# (operator, dataset, variable, label shown under the title, colour-bar label, scale to plot units)
CONTINUOUS = [
    ("mean", "itaituba", "elevation", "elevation", "m", 1.0),
    ("percentage", "itaituba", "defor_87", "defor_87", "share of the cell", 1.0),
    ("distance", "itaituba", "distroad", "distroad", "km", 1e-3),
]
CATEGORICAL = ("majority", "majority", "defor_mode", "defor_mode")

SEQUENTIAL = "Blues"
CLASS_COLOURS = {7: "#4c78a8", 87: "#f58518", 167: "#54a24b", 255: "#b279a2"}


def _load(dataset: str, workspace_root: Path):
    ds = tomllib.loads((HERE / f"{dataset}.compare.toml").read_text(encoding="utf-8"))["dataset"]
    ref = _load_reference(ds)
    ws = workspace_root / dataset
    cube = CubeClient(str(ws / "catalog.db"), str(ws / "store"))
    grid = cube.catalog.get_grid(ds["grid"])
    rows, cols, ok = _cells(cube, ds["grid"], ref)
    return ds, ref, cube, grid, rows[ok], cols[ok], ok


def _plane(grid, rows, cols, values) -> np.ndarray:
    a = np.full((grid.rows, grid.cols), np.nan)
    a[rows, cols] = values
    return a


def _first_class(cell) -> float:
    """TerraME writes one class or, on a tie, every tied class ("7,87"); DisSCube takes the smallest."""
    s = str(cell).strip()
    return float(min(float(t) for t in s.split(","))) if s and s.lower() != "nan" else np.nan


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace-root", type=Path, default=HERE / "data")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--dpi", type=int, default=300)
    args = p.parse_args()

    fig, axes = plt.subplots(2, 4, figsize=(7.0, 3.5), dpi=args.dpi)
    fig.subplots_adjust(left=0.07, right=0.995, top=0.9, bottom=0.24, wspace=0.06, hspace=0.02)

    for j, (operator, dataset, var, label, unit, scale) in enumerate(CONTINUOUS):
        ds, ref, cube, grid, rows, cols, ok = _load(dataset, args.workspace_root)
        ours = _plane(grid, rows, cols, cube.load(var, grid_id=ds["grid"]).to_numpy()[rows, cols] * scale)
        theirs = _plane(grid, rows, cols, ref[var].to_numpy()[ok] * scale)
        vmin = float(np.nanmin([np.nanmin(ours), np.nanmin(theirs)]))
        vmax = float(np.nanmax([np.nanmax(ours), np.nanmax(theirs)]))
        for i, arr in enumerate((ours, theirs)):
            im = axes[i, j].imshow(arr, cmap=SEQUENTIAL, vmin=vmin, vmax=vmax, interpolation="nearest")
        diff = np.nanmax(np.abs(ours - theirs))
        cax = fig.add_axes([0.07 + j * 0.2325 + 0.015, 0.13, 0.2325 - 0.045, 0.018])
        cb = fig.colorbar(im, cax=cax, orientation="horizontal")
        cb.ax.tick_params(labelsize=6, length=2)
        cb.outline.set_linewidth(0.3)
        cb.set_label(f"{label} ({unit})", fontsize=6.5, labelpad=1)
        axes[0, j].set_title(operator, fontsize=8.5, fontweight="bold", pad=3)
        axes[1, j].text(0.5, -0.07, f"max |diff| = {diff:.3g} {unit if unit != 'share of the cell' else ''}".strip(),
                        transform=axes[1, j].transAxes, ha="center", va="top", fontsize=6.5, color="#444444")

    # majority: predominant class (categorical)
    operator, dataset, var, label = CATEGORICAL
    ds, ref, cube, grid, rows, cols, ok = _load(dataset, args.workspace_root)
    ours = _plane(grid, rows, cols, cube.load(var, grid_id=ds["grid"]).to_numpy()[rows, cols])
    theirs = _plane(grid, rows, cols, np.array([_first_class(v) for v in ref[var].to_numpy()[ok]]))
    classes = sorted({int(v) for v in np.unique(np.concatenate([ours[~np.isnan(ours)], theirs[~np.isnan(theirs)]]))})
    colours = [CLASS_COLOURS.get(c, "#9a9a9a") for c in classes]
    cmap = ListedColormap(colours)
    norm = BoundaryNorm(np.arange(len(classes) + 1) - 0.5, cmap.N)
    index = {c: k for k, c in enumerate(classes)}
    for i, arr in enumerate((ours, theirs)):
        idx = np.vectorize(lambda v: index.get(int(v), np.nan) if not np.isnan(v) else np.nan)(arr)
        axes[i, 3].imshow(idx, cmap=cmap, norm=norm, interpolation="nearest")
    both = ~np.isnan(ours) & ~np.isnan(theirs)
    agree = 100 * float(np.mean(ours[both] == theirs[both]))
    axes[0, 3].set_title(operator, fontsize=8.5, fontweight="bold", pad=3)
    axes[1, 3].text(0.5, -0.07, f"{agree:.1f}% of cells agree", transform=axes[1, 3].transAxes,
                    ha="center", va="top", fontsize=6.5, color="#444444")
    fig.legend(handles=[Patch(facecolor=c, edgecolor="#666666", linewidth=0.4, label=str(k))
                        for k, c in zip(classes, colours)],
               loc="lower right", bbox_to_anchor=(0.995, 0.0), ncol=len(classes), fontsize=6.5, frameon=False,
               title=f"{label} (class)", title_fontsize=6.5, handlelength=1.2, columnspacing=0.8)

    for ax in axes.ravel():
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    for i, name in enumerate(("DisSCube", "TerraME")):
        axes[i, 0].set_ylabel(name, fontsize=8.5, fontweight="bold", labelpad=3)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi)
    print(f"{args.out}: 4 operators, {grid.rows} x {grid.cols} cells of {grid.resolution / 1000:g} km")


if __name__ == "__main__":
    main()
