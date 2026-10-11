"""Node costs by the algorithm of the aRT package (R-TerraLib, 2014; R/gpmFunctions.R), for comparison.

    python art_gpm_costs.py --roads roads.shp --ports ports.shp --out nodes_art.csv

aRT builds the graph from the ENDS of each line only (one edge per line, weight = weighted length of the whole
line: createConnectivityMatrix), gives every port to the nearest end node with the out-of-network cost
(initNodesDistance), and then sweeps over the nodes, replacing a node cost by the minimum over its neighbours of
neighbour cost + edge weight, until no node improves (updateDistances). This script follows that, and then derives
the cost of the interior vertices of each line from the two end costs (min of the two ways along the line), so that
the result can be checked with check_shortest_path.py. The entry rule differs from the TerraME 2.0 Network (nearest
end node instead of the closest point of a line), so costs near the ports differ by construction.
"""
import argparse
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--roads", type=Path, required=True)
    p.add_argument("--ports", type=Path, required=True)
    p.add_argument("--factor", default="custo_ajus")
    p.add_argument("--scale", type=float, default=1e-3, help="metres to km")
    p.add_argument("--outside", type=float, default=2.0, help="factor of the out-of-network distance")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    roads = gpd.read_file(a.roads)
    ports = gpd.read_file(a.ports).to_crs(roads.crs)
    key = lambda xy: (round(float(xy[0]), 3), round(float(xy[1]), 3))
    lines = []  # (end a, end b, vertices, factor)
    for g, f in zip(roads.geometry, roads[a.factor], strict=True):
        for part in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            xy = np.array(part.coords)
            lines.append((key(xy[0]), key(xy[-1]), xy, float(f)))
    adj = defaultdict(list)
    for ka, kb, xy, f in lines:
        w = float(np.hypot(*np.diff(xy, axis=0).T).sum()) * f * a.scale
        adj[ka].append((kb, w))
        adj[kb].append((ka, w))
    nodes = list(adj)
    cost = dict.fromkeys(nodes, 1e15)
    xy_nodes = np.array(nodes)
    for pt in ports.geometry:
        d = np.hypot(*(xy_nodes - np.array([pt.x, pt.y])).T)
        j = int(d.argmin())
        cost[nodes[j]] = min(cost[nodes[j]], float(d[j]) * a.scale * a.outside)

    sweeps = 0
    changed = True
    while changed:  # updateDistances: repeat until no node improves
        changed = False
        sweeps += 1
        for n in nodes:
            best = min(cost[m] + w for m, w in adj[n])
            if best < cost[n]:
                cost[n], changed = best, True

    rows = {}
    for ka, kb, xy, f in lines:
        step = np.hypot(*np.diff(xy, axis=0).T) * f * a.scale
        s = np.concatenate([[0.0], np.cumsum(step)])
        for (x, y), si in zip(xy, s, strict=True):
            c = min(cost[ka] + si, cost[kb] + s[-1] - si)
            k = key((x, y))
            rows[k] = min(rows.get(k, 1e15), c)
    with a.out.open("w") as fh:
        fh.write("x,y,cost\n")
        for (x, y), c in rows.items():
            fh.write(f"{x:.3f},{y:.3f},{c:.6f}\n")
    print(f"{len(nodes)} end nodes, {len(rows)} nodes written, {sweeps} sweeps -> {a.out}")


if __name__ == "__main__":
    main()
