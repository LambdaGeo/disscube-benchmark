"""Compare the node costs of DisSCube and TerraME (output of export_nodes_*.py / .lua).

    python compare_nodes.py nodes_disscube.csv nodes_terrame.csv --out nodes_compare.csv

Nodes are matched by position (nearest within --tol metres, default 0.5), because TerraME shifts
some target nodes by 0.01 and adds middle nodes that DisSCube does not have. Prints how many nodes
match, the nodes that exist on one side only, and the statistics of the difference
(DisSCube minus TerraME, km); writes every matched node with its difference.

With --cells it also rebuilds the cell costs from each set of nodes by the vertex rule (cost of the nearest
node plus the off-network distance times the factor of connectivity.toml) and compares them with the
golden. That separates the two possible sources of the difference: the node costs and the way a cell
enters the network.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tomllib
from scipy.spatial import cKDTree


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("disscube", type=Path)
    p.add_argument("terrame", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--tol", type=float, default=0.5)
    p.add_argument("--cells", action="store_true", help="also rebuild the cell costs and compare them with the golden")
    p.add_argument("--pipeline", type=Path, default=Path(__file__).parents[1] / "connectivity.toml")
    p.add_argument("--spec", type=Path, default=Path(__file__).parents[1] / "connectivity.compare.toml")
    a = p.parse_args()

    d, t = pd.read_csv(a.disscube), pd.read_csv(a.terrame)
    dist, j = cKDTree(t[["x", "y"]].to_numpy()).query(d[["x", "y"]].to_numpy(), distance_upper_bound=a.tol)
    hit = np.isfinite(dist)
    m = d[hit].copy()
    m["cost_terrame"] = t["cost"].to_numpy()[j[hit]]
    m["diff"] = m["cost"] - m["cost_terrame"]
    m = m.rename(columns={"cost": "cost_disscube"})
    print(f"DisSCube nodes {len(d)}, TerraME nodes {len(t)}, matched {len(m)} "
          f"({len(d) - len(m)} only in DisSCube, {len(t) - len(m)} only in TerraME)")
    q = m["diff"].describe(percentiles=[.01, .05, .5, .95, .99])
    print("difference DisSCube - TerraME (km):\n", q.round(2).to_string())
    print("nodes with |diff| > 1 km:", int((m["diff"].abs() > 1).sum()),
          " > 25 km:", int((m["diff"].abs() > 25).sum()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(a.out, index=False, float_format="%.6f")
    print("written:", a.out)
    if a.cells:
        _cells_check(a, d, t)


def _cells_check(a: argparse.Namespace, d: pd.DataFrame, t: pd.DataFrame) -> None:
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from compare import _load_reference

    par = next(x for x in tomllib.loads(a.pipeline.read_text())["derive"] if x["target"] == "cost")["params"]
    k = float(par["outside"]) * float(par["unit_scale"])
    ref = _load_reference(tomllib.loads(a.spec.read_text())["dataset"])
    gold = ref["cost"].to_numpy()
    print("\ncell costs rebuilt from the nodes (vertex rule) against the golden, km:")
    for name, nodes in (("TerraME nodes", t), ("DisSCube nodes", d)):
        dist, j = cKDTree(nodes[["x", "y"]].to_numpy()).query(ref[["cx", "cy"]].to_numpy())
        e = dist * k + nodes["cost"].to_numpy()[j] - gold
        print(f"  {name:15s} mean |error| {np.abs(e).mean():6.2f}  max {np.abs(e).max():6.1f}  "
              f"within 0.01: {np.mean(np.abs(e) < 0.01):.1%}  within 1: {np.mean(np.abs(e) < 1):.1%}")


if __name__ == "__main__":
    main()
