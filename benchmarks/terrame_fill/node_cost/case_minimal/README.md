# Minimal case: 8 lines, 9 segments, 1 port; a TerraME node cost that is not a shortest path

Found by generating random road networks (5 x 5 grid of junctions, jittered, lines meeting only at their endpoints,
one port) and running the TerraME 2.0.1 / pinned GPM `Network` on each: 1 of 30 networks broke the shortest-path
condition. That network (36 lines) was reduced by removing lines, and then interior vertices, while the break
persisted: 8 lines (only one has an interior vertex) and 1 port. Cost per segment = length in km x `custo_ajus`;
the cost outside the network is `distance * 1e-3 * 2`, as in the connectivity case.

The shapefiles (the case and the TerraView version) are in `shapefiles.zip`; run `unzip shapefiles.zip` here first
(it creates `roads.*`, `port.*` and the shapefiles of `terraview/`).

Files: `roads.shp` (8 lines, field `custo_ajus`), `port.shp`, `nodes_terrame.csv` (the TerraME node costs),
`export_nodes_terrame_env.lua` (run with `ROADS=... PORTS=... OUT=...`), `check_segments.py`,
`terraview/` (the same case for the old TerraView, see its README).

Result: the port enters the network at P (5023016.97, 9774556.23) with cost 2.79. Line 2 has three points: its first end, the
vertex V (4976150.84, 9802438.79) and the junction J (4979578.81, 9822998.81). From P the exact shortest path costs
36.93 km to J and 49.37 km to V (V is reached through J). TerraME gives J = 36.93 (correct) and V = 56.75, which is 7.38 km
more than J's cost plus the segment V-J: V kept the cost that arrived from the other end of its line, and the cheaper cost
through J did not reach it.

After `unzip shapefiles.zip`, `python3 check_segments.py` lists the break (needs geopandas, pandas, numpy).
