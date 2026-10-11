"""Cost of every node of the road graph, as DisSCube computes it (NetworkCostOperator, disscube 0.5.0).

    python export_nodes_disscube.py --workspace ../data/connectivity --out nodes_disscube.csv

Builds the same graph as the operator (nodes keyed by coordinates rounded to 1 mm, one edge per
segment, cost = length x factor x unit_scale), joins each port to its nearest node with the access cost
outside x unit_scale, and writes the Dijkstra cost of each node. Columns: x, y, cost, target (index of
the port that gives the minimum). The parameters are read from connectivity.toml, so they cannot
differ from the run.
"""
import argparse
import itertools
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import tomllib
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import Point


def _path(workspace: Path, name: str) -> Path:
    return Path(json.loads((workspace / "raw" / f"{name}.provenance.json").read_text())["path"])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--pipeline", type=Path, default=Path(__file__).parents[1] / "connectivity.toml")
    args = p.parse_args()

    par = next(d for d in tomllib.loads(args.pipeline.read_text())["derive"] if d["target"] == "cost")["params"]
    crs, scale, outside, col = par["crs"], float(par["unit_scale"]), float(par["outside"]), par["cost_column"]
    roads = gpd.read_file(_path(args.workspace, "roads")).to_crs(crs)
    ports = gpd.read_file(_path(args.workspace, "ports")).to_crs(crs)

    keys: dict[tuple[float, float], int] = {}
    pts: list[Point] = []

    def node(pt: Point) -> int:
        k = (round(pt.x, 3), round(pt.y, 3))
        if k not in keys:
            keys[k] = len(keys)
            pts.append(Point(pt.x, pt.y))
        return keys[k]

    rows, cols_, cost = [], [], []
    for _, r in roads.iterrows():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        factor = float(r[col]) if col in r and not pd.isna(r[col]) else 1.0
        for line in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            xy = list(line.coords)
            for a, b in itertools.pairwise(xy):
                pa, pb = Point(a), Point(b)
                d = pa.distance(pb)
                if d == 0:
                    continue
                u, v = node(pa), node(pb)
                rows += [u, v]
                cols_ += [v, u]
                cost += [d * factor * scale] * 2
    n = len(pts)
    adj = csr_matrix((cost, (rows, cols_)), shape=(n, n))
    tree = shapely.STRtree(pts)
    tgt = [g if g.geom_type == "Point" else g.centroid for g in ports.geometry if g is not None and not g.is_empty]
    idx = [int(np.atleast_1d(tree.query_nearest(t))[0]) for t in tgt]
    pen = np.array([t.distance(pts[i]) * outside * scale for t, i in zip(tgt, idx, strict=True)])[:, None]
    dist = dijkstra(adj, indices=idx, directed=False) + pen
    best = np.argmin(dist, axis=0)
    out = pd.DataFrame({"x": [q.x for q in pts], "y": [q.y for q in pts],
                        "cost": dist[best, np.arange(n)], "target": best})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, float_format="%.6f")
    print(f"{args.out}: {n} nodes, {len(tgt)} ports, {int(np.isinf(out.cost).sum())} unreachable")


if __name__ == "__main__":
    main()
