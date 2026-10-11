"""List the segments of roads.shp whose two nodes (nodes_terrame.csv) differ in cost by more than the segment cost."""
import itertools

import geopandas as gpd
import numpy as np
import pandas as pd


def check(roads_path, nodes_path, tol=0.001):
    roads = gpd.read_file(roads_path)
    nodes = pd.read_csv(nodes_path)
    cost = {(round(x, 3), round(y, 3)): c for x, y, c in zip(nodes.x, nodes.y, nodes.cost, strict=True)}
    bad, total = [], 0
    for fid, row in roads.iterrows():
        xy = list(row.geometry.coords)
        for a, b in itertools.pairwise(xy):
            ka, kb = (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3))
            if ka in cost and kb in cost:
                w = np.hypot(a[0] - b[0], a[1] - b[1]) * 1e-3 * row.custo_ajus
                total += 1
                excess = abs(cost[ka] - cost[kb]) - w
                if excess > tol:
                    bad.append((fid, round(excess, 2), ka, kb))
    return total, bad


if __name__ == "__main__":
    total, bad = check("roads.shp", "nodes_terrame.csv")
    print(total, "segments checked;", len(bad), "break the shortest-path condition:")
    for fid, excess, a, b in bad:
        print("  line", fid, "excess", excess, "km between", a, "and", b)
