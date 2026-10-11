"""Do the node costs of a network satisfy the shortest-path condition on the road graph?

    python check_shortest_path.py nodes_terrame.csv --workspace ../data/connectivity
    python check_shortest_path.py nodes_disscube.csv --workspace ../data/connectivity

In an exact shortest-path solution, two nodes joined by a road segment cannot differ in cost by more than
the cost of the segment (length x factor x unit_scale): |cost(u) - cost(v)| <= w(u, v). The script counts the
segments that break this, how large the breaks are and where they sit in their line (first or last segment,
which is where two lines meet, or an interior one). Nodes are read by position (0.5 m), so the file can come
from either implementation.
"""
import argparse
import itertools
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import tomllib
from scipy.spatial import cKDTree


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("nodes", type=Path, help="x, y, cost (km) of every node")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--pipeline", type=Path, default=Path(__file__).parents[1] / "connectivity.toml")
    p.add_argument("--slack", type=float, default=1e-3, help="km tolerated before a segment counts as a break")
    a = p.parse_args()

    par = next(d for d in tomllib.loads(a.pipeline.read_text())["derive"] if d["target"] == "cost")["params"]
    scale, col = float(par["unit_scale"]), par["cost_column"]
    prov = json.loads((a.workspace / "raw" / "roads.provenance.json").read_text())["path"]
    roads = gpd.read_file(prov).to_crs(par["crs"])
    nodes = pd.read_csv(a.nodes)
    tree, cost = cKDTree(nodes[["x", "y"]].to_numpy()), nodes["cost"].to_numpy()

    u, v, w, at_end = [], [], [], []
    for g, f in zip(roads.geometry, roads[col], strict=True):
        for line in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            xy = np.array(line.coords)
            segs = [(p0, p1) for p0, p1 in itertools.pairwise(xy) if np.hypot(*(p0 - p1)) > 0]
            for i, (p0, p1) in enumerate(segs):
                u.append(p0)
                v.append(p1)
                w.append(np.hypot(*(p0 - p1)) * f * scale)
                at_end.append(i in (0, len(segs) - 1))
    u, v, w, at_end = np.array(u), np.array(v), np.array(w), np.array(at_end)
    du, iu = tree.query(u)
    dv, iv = tree.query(v)
    ok = (du < 0.5) & (dv < 0.5)
    excess = (np.abs(cost[iu] - cost[iv]) - w)[ok]
    bad = excess > a.slack
    end = at_end[ok]
    print(f"{a.nodes}: {int(ok.sum())} segments read, {int(bad.sum())} break the condition "
          f"({bad.mean():.2%}) by more than {a.slack} km")
    if bad.any():
        print(f"  size of the breaks (km): median {np.median(excess[bad]):.2f}, "
              f"95th percentile {np.percentile(excess[bad], 95):.1f}, maximum {excess[bad].max():.1f}")
        print(f"  first or last segment of its line: {end[bad].mean():.1%} of the breaks "
              f"({end.mean():.1%} of all segments)")


if __name__ == "__main__":
    main()
