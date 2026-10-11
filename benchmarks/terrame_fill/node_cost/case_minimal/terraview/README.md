# Test of the 8-line case with the TerraLib 3/4 open-network GPM

The shapefiles listed here are in `../shapefiles.zip` (`unzip ../shapefiles.zip` from this folder's parent); the CSV files are here.

Files: `roads_cost.shp` (8 lines; `cost_total` = length in km x `custo_ajus`, the cost of the whole line, which is what
`TeGraphNetwork(lines, cost_attribute)` takes), `cells3.shp` (three 1 km squares with ids P, V, J; SIRGAS 2000 Polyconic, EPSG:5880).

The centroid of P is the point of the network nearest to the port (so the cost outside the network is zero), V is the interior
vertex that TerraME costs wrongly, and J is the junction at the end of the same line.

Any tool built on TerraLib 3/4 `TeGraphNetwork` + `TeProxMatrixOpenNetworkStrategy` can be used: load the two layers, build the
open-network GPM with cells = `cells3`, lines = `roads_cost`, cost attribute = `cost_total`, maxlocal = 0 and large values for
max network distance and max connections, and save the GPM (text, GWT and GAL files).

Expected from an exact shortest path on this graph (km, from P): to J 36.932, to V 49.373.
TerraME 2.0.1 gives (its node costs minus the 2.79 at P): J 36.93 and V 56.75.
The GWT file stores weights, not distances (inverse-distance weighting in the TerraLib strategy),
so the distances have to be read back from the three files.

## Version with 21 cells (`cells21.shp`)

`cells21.shp`: 7 x 3 square cells of 20 km (ids `C<col>_<row>`), covering the 8 lines (EPSG:5880). Use it in place of `cells3.shp`
if you want a GPM with all cells; the cells with ids P, V and J of `cells3.shp` remain the test of the node costs.

* `cells21_terrame.csv`: cost of each cell to the port from TerraME 2.0.1 (`GPM{destination = network, origin = cells,
  entrance = "lowest", by = "points"}`, `fill{strategy = "minimum"}`; outside factor 2, inside = km x `custo_ajus`).
* `cells21_reference.csv`: for comparison, the cell cost computed here with exact shortest-path costs at the network nodes
  and the cell entering the nearest point of each line (`exact_nearest_point_rule`), and the same rule on the TerraME node
  costs (`terrame_nodes_nearest_point_rule`). This rule is ours: TerraME's entry rule is not the same (the cell values differ
  from this reference in both directions, -5.3 to +12.6 km, also where the node costs are right), so the differences between
  TerraME and this table are NOT evidence of the node-cost problem. The test that isolates it is the P-V-J test above.

## Point layers

* `points_port_P_V_J.shp`: the port, its entry into the network (P), the vertex V and the junction J.
* `network_nodes.shp`: the 9 nodes of the network (`role` = port_entry, line_end or vertex) with the exact cost from the port (including the 2.79 km of the port to P)
  (`exact_km`, includes the 2.79 km from the port to P), the cost of TerraME 2.0.1 (`terrame_km`) and the difference; only V differs (+7.38 km).
* `cells21_centroids.shp`: the centroids of the 21 cells.
