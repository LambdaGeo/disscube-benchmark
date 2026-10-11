"""Figure: generalized transport cost to the ports, DisSCube (A) and TerraME (B), same cells, same classes.

    disscube run connectivity.toml --workspace data/connectivity
    python figure_connectivity.py --workspace data/connectivity --out reports/connectivity/fig_connectivity_cost.png

The TerraME values are the golden of luccme-goldens (read as compare.py reads it, with the same SHA-256
check); the DisSCube values are the `cost` variable of the workspace. Both panels use the cells of the
golden and the same class limits, so differences in the picture are differences in the values.
Roads and ports are the files the run fetched (their paths are in <workspace>/raw/*.provenance.json).
"""
import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import tomllib
from compare import _cells, _load_reference
from disscube import CubeClient
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# Class limits and greys of the published figure (QGIS discrete colour map: a value belongs to the
# class whose upper limit it does not exceed). Generalized transport cost, km.
UPPER = [129, 249, 466, 797]
GREYS = ["#fafafa", "#bdbdbd", "#808080", "#424242", "#050505"]
LABELS = ["3 - 129", "129 - 249", "249 - 466", "466 - 797", "797 - 2519"]


# Difference DisSCube minus TerraME (km): negative = DisSCube lower. Classes chosen around the dominant
# offset of about -25 km (see the report of the case).
DIFF_UPPER = [-100, -25, -5, 5, 25]
DIFF_COLORS = ["#2166ac", "#67a9cf", "#d1e5f0", "#ededed", "#fddbc7", "#b2182b"]
DIFF_NAMES = ["below -100", "-100 to -25", "-25 to -5", "-5 to 5", "5 to 25", "above 25"]


def _classes(a: np.ndarray, upper: list[float] = UPPER) -> np.ma.MaskedArray:
    idx = np.digitize(a, upper, right=True).astype(float)
    return np.ma.masked_where(np.isnan(a), idx)


def _source_path(workspace: Path, name: str) -> Path:
    return Path(json.loads((workspace / "raw" / f"{name}.provenance.json").read_text())["path"])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--spec", type=Path, default=Path(__file__).with_name("connectivity.compare.toml"))
    p.add_argument("--dpi", type=int, default=300)
    args = p.parse_args()

    ds = tomllib.loads(args.spec.read_text(encoding="utf-8"))["dataset"]
    ref = _load_reference(ds)
    cube = CubeClient(str(args.workspace / "catalog.db"), str(args.workspace / "store"))
    grid = cube.catalog.get_grid(ds["grid"])
    rows, cols, ok = _cells(cube, ds["grid"], ref)
    rows, cols = rows[ok], cols[ok]
    xmin, _, _, ymax = grid.bbox

    ours = np.full((grid.rows, grid.cols), np.nan)
    theirs = np.full((grid.rows, grid.cols), np.nan)
    ours[rows, cols] = cube.load("cost", grid_id=ds["grid"]).to_numpy()[rows, cols]
    theirs[rows, cols] = ref["cost"].to_numpy()[ok]

    # crop to the cells that exist
    # The view stops at the mainland: isolated cells east of the first gap of more than 5 empty columns
    # (islands) are in the data and in the comparison, but are left out of the view.
    uniq = np.unique(cols)
    gaps = np.where(np.diff(uniq) > 5)[0]
    cmax = uniq[gaps[0]] if len(gaps) else uniq[-1]
    r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cmax + 1
    res = grid.resolution
    extent = (xmin + c0 * res, xmin + c1 * res, ymax - r1 * res, ymax - r0 * res)

    diff = ours - theirs
    share = [100 * np.mean(np.digitize(diff[rows, cols], DIFF_UPPER, right=True) == k) for k in range(6)]
    roads = gpd.read_file(_source_path(args.workspace, "roads"))
    ports = gpd.read_file(_source_path(args.workspace, "ports"))

    fig = plt.figure(figsize=(6.3, 6.4), dpi=args.dpi)
    grid_spec = fig.add_gridspec(2, 2, left=0.01, right=0.99, top=0.945, bottom=0.015, wspace=0.02, hspace=0.12)
    ax_a, ax_b, ax_c, ax_l = (fig.add_subplot(grid_spec[i, j]) for i in (0, 1) for j in (0, 1))
    panels = (
        (ax_a, ours, "A  DisSCube", ListedColormap(GREYS), UPPER, True),
        (ax_b, theirs, "B  TerraME", ListedColormap(GREYS), UPPER, True),
        (ax_c, diff, "C  DisSCube minus TerraME", ListedColormap(DIFF_COLORS), DIFF_UPPER, False),
    )
    for ax, arr, title, cmap, upper, with_roads in panels:
        ax.imshow(_classes(arr[r0:r1, c0:c1], upper), cmap=cmap, norm=BoundaryNorm(np.arange(-0.5, cmap.N + 0.5), cmap.N),
                  extent=extent, interpolation="nearest", origin="upper")
        if with_roads:
            roads.plot(ax=ax, color="#e58fa0", linewidth=0.12, zorder=3)
        ports.plot(ax=ax, color="#3b6fb6", edgecolor="#1d3f73", markersize=9, linewidth=0.4, zorder=4)
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_axis_off()
        ax.set_title(title, fontsize=9, loc="left", fontweight="bold", pad=2)

    ax_l.set_axis_off()
    cost = [Patch(facecolor=c, edgecolor="#666666", linewidth=0.4, label=lab) for c, lab in zip(GREYS, LABELS)]
    cost += [Line2D([], [], marker="o", linestyle="", markerfacecolor="#3b6fb6", markeredgecolor="#1d3f73",
                    markersize=5, label="Ports"),
             Line2D([], [], color="#e58fa0", linewidth=1, label="Roads")]
    leg1 = ax_l.legend(handles=cost, loc="upper left", fontsize=7, frameon=False, bbox_to_anchor=(0.0, 1.0),
                       title="A, B: generalized transport cost\nto the nearest port (km)", title_fontsize=7.5,
                       alignment="left")
    ax_l.add_artist(leg1)
    delta = [Patch(facecolor=c, edgecolor="#666666", linewidth=0.4, label=f"{n}  ({v:.1f}% of cells)")
             for c, n, v in zip(DIFF_COLORS, DIFF_NAMES, share)]
    ax_l.legend(handles=delta, loc="lower left", fontsize=7, frameon=False, bbox_to_anchor=(0.0, 0.0),
                title="C: difference in cost (km);\nnegative = DisSCube lower", title_fontsize=7.5, alignment="left")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi)
    print(f"{args.out}: {len(rows)} cells ({int((cols > cmax).sum())} outside the view), upper limits {UPPER}")


if __name__ == "__main__":
    main()
