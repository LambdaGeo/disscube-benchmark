# Case record: one TerraME node cost that is not a shortest path (247.6 km)

Offered for joint examination with the TerraME/LuccME developers. We do not claim that
either implementation is right for this variable; this record shows where, in the code of
the GPM `Network` module, one departure from the shortest-path condition arises.

## The case

Road network of the connectivity case (BR-163, feature 16529; 14 ports; EPSG:5880; costs in km).
A = last vertex of feature 16529, (4915052.14, 9706076.48).
J = junction of features 16529, 16530 and 16534, (4916685.91, 9709263.31).
The segment A-J has cost 0.71 km. At the end of the run the node costs are
A = 329.758 and J = 578.114, so |cost(J) - cost(A)| = 248.4 > 0.71 (the excess over the
segment is 247.6 km). Through A, J would cost 329.758 + 0.71 = 330.47.

## What the log shows (`trace.log`, 85 lines)

1. Steps 1-21: the nodes are created with costs of about 633-636 km, from target 1.
2. Steps 22-50: `reviewNextNodes` lowers J and the nodes of 16534 to about 580 km, from target 7
   (J.next = v2 of 16534), and the cascade gives A 580.742 (A.next = J).
3. Steps 51-65: `reviewCircularPrevious` runs along the chain v0 -> v3 -> A of feature 16529 and
   lowers v0 to 330.092, v3 to 330.941 and A to 331.674 (A.next becomes v3, so A.previous = J).
4. Step 70: the same function is called with node = A and prev = J. `validateCircularPrevious`
   returns nil (`link=nil`), so nothing is propagated to J. State at that moment:
   `A.previous = J` (simple); `J.router = true`, `J.previous = {v1 of 16530, A}`.
5. Steps 66-79: `reviewPreviousNodes` applies a uniform correction of 1.916 km to all of them
   (J 578.114, A 329.758). J keeps the value that came from the other side.

## Why `validateCircularPrevious` returns nil (reading of the code, Network.lua)

The function recognises "A points to J and J points to A". When `node` is a simple node and
`prev` is a router (branch `elseif prev.router`), it calls

    isPreviousCircular(node, prev.previous[i])

which tests `node.previous.id == prev.previous[i].id and prev.previous[i].previous.id == node.id`.
Here `prev.previous[i]` is A itself, so the test compares A.previous (= J) with A and fails.
Even with the arguments swapped, `isPreviousCircular(A, J)` needs `J.previous.id`, and the
previous of J is a table (a router), so it is nil. In the log the call returns `link=nil`
at steps 70 and 85. The other branches (`ROUTER_ROUTER`, `SIMPLE_ROUTER`) are marked
`-- SKIP` ("no test data for this") in the source, which agrees with the case not being
covered by the module's tests. The body of the `SIMPLE_ROUTER` branch also indexes
`node.previous[k]` where `previous.previous[k]` seems intended; we have not tested a fix.

Consequence: a lower cost that reaches the end of a line through the chain of one line is not
carried across the junction to the router node, which keeps the cost that arrived by another
line. This is consistent with the 827-828 violating segments (all at the first or last segment of a
line, `../check_shortest_path.py`), but we traced one case, not all of them.

## Reproduce

* `Network_trace.diff`: the diagnostic changes to the pinned `Network.lua` (terrame-docker 0.4.2,
  TerraME 2.0.1): a log of every write to the watched nodes, and the state at each call of
  `reviewCircularPrevious`. It does not change the computation.
* Run `export_nodes_terrame.lua` (see `../README.md`) with the patched file; `trace.log` is written
  to the working directory.

## A first correction, tested (experiment, not a proposal)

`Network_fix_experiment.diff` makes `validateCircularPrevious` recognise "A.previous is J and J.previous
contains A" (new link `SIMPLE_ROUTER_FIX`) and, in `reviewCircularPrevious`, lowers J through A as the
simple-node branch does, then revises J's previous nodes. Result on the same inputs (the pinned
TerraME 2.0.1 / GPM): this case is repaired (A 302.96, J 303.67; the segment costs 0.71), but the number of
segments that break the shortest-path condition goes from 827 to 873 (maximum 247.6 to 246.9 km), still all
at the first or last segment of a line. The route of the missing propagation is therefore not unique: other
junction cases pass through other paths of the revision, and a correct fix probably needs the
junction handled as a whole rather than patched in one branch. Counts use a tolerance of 0.001 km.

## Is the result the same in every run? Almost (11 Oct 2026)

Six runs of `../export_nodes_terrame.lua` with the same binary, gpm and inputs (original `Network.lua`): 827 segments break
the condition in four runs and 828 in two; the node count is 119,331 in all of them and the node costs differ in one node
(up to 27 km) from one run to another. The counts of this record (827) are those of the runs in which it was measured; the
cause of the small variation between runs was not investigated.

## Is it the number of ports? No (10 Oct 2026)

`export_nodes_ports_subset.lua` is the export with the ports taken from the environment variable `PORTS`
(a shapefile) and the output from `OUT`. Segments that break the shortest-path condition
(`../check_shortest_path.py`, tolerance 0.001 km), same roads, original GPM:

| ports | segments that break the condition |
|---|---|
| each of the 14 ports alone | 494 to 720 (0.41% to 0.60%) |
| first 2 / 4 / 8 | 599 / 606 / 712 |
| all 14 | 827 |

With a single target the network still breaks the condition in 0.4-0.6% of the segments, always at the first
or last segment of a line. The cause is therefore in how a cost is revised at the junctions between lines,
not in the interaction between ports.

## Does the order of the lines matter? Yes (10 Oct 2026)

With the same roads, ports and GPM, only the order of the features in `br_roads_5880.shp` changed
(`export_nodes_ports_subset.lua` with `ROADS=...`), all 14 ports:

| order | segments that break the condition | largest break (km) | nodes in the file |
|---|---|---|---|
| original | 827 | 247.6 | 119,331 |
| reversed | 1,286 | 247.6 | 119,331 |
| random 1 to 4 | 434, 508, 472, 446 | 66.8, 135.5, 126.1, 129.6 | 119,330 to 119,331 |

Node costs differ from the original order by more than 0.01 km in 84,000 to 98,000 of the nodes (up to 294 km).
An exact shortest-path solution does not depend on the order of the lines. This agrees with a network built
and revised incrementally, where the result depends on the order in which lines are added.

See also `../case_minimal/` for a network of 8 lines that reproduces the break.

## An earlier GPM implementation (aRT 1.9-2, 2014)

`../art_gpm_costs.py` follows the algorithm of `R/gpmFunctions.R` of the R package aRT (read, not run):
one edge per line between its two ends, ports given to the nearest end node, and a sweep over the nodes repeated
until none improves (`updateDistances`), which gives shortest paths of the end-node graph. On the same roads and
ports it breaks the shortest-path condition in 0 of 120,292 segments (TerraME 2.0.1: 827) and has 116,824 nodes
(the DisSCube graph; TerraME: 119,331). Compared by position: aRT-style minus DisSCube has median 0.00 km,
mean +2.26, range -1.43 to +13.70 (49.3% within 0.01 km; the excess is near the ports, where aRT-style enters at
the nearest line end); aRT-style minus TerraME has median -0.87 km, range -274.4 to +13.8.
The thesis that defines the variable (Aguiar, 2006, p. 45) calls it inversely proportional to the shortest path.

## Public repository

`lua/Network.lua` of github.com/TerraME/gpm (master, version 0.6, last commit 3aa0e91 of 6 Dec 2019; the file
last changed on 30 Aug 2019) is byte-identical to the file of the TerraME 2.0.1 image used here.

## TerraLib 5.7.2 (checked, `src/terralib/sa`, `graph`, `qt/plugins/sa`)

No shortest-path or network-cost code. The GPM of TerraLib 5 (`te::sa::GeneralizedProximityMatrix`) is built by
adjacency, distance or nearest neighbours; `GPMWeightsInverseDistanceStrategy.cpp` and
`GPMWeightsSquaredInverseDistanceStrategy.cpp` carry commented-out lines under "extra information calculate in
TerraLib 4" (`WasNetworkObjectsDistanceComputed`, `NetworkObjectsDistance`, `WasNetworkMinimumPathComputed`,
`NetworkMinimumPath`): the network minimum path was an attribute of the TerraLib 4 GPM and was not ported.
`te::graph` has builders (flow, LDD, region adjacency, query) and no Dijkstra.

## Lineage of the open-network GPM (from the sources we could read)

* TerraLib 3/4 (C++): `TeGraphNetwork` and `TeProxMatrixOpenNetworkStrategy` (see the TerraLib 4.2.2 section below).
* aRT 1.9-2 (R): `createOpenNetwork`, `getNeighborsOpenNetworkFunction`; its vignette states a known limitation
  "when the entry point on the network for a given point is the start or end of a line segment".
* TerraME gpm 0.6 (Lua): `Network`, the version tested here.

## TerraView 3.2.0 (Windows binaries, 2008; no sources)

`terralib.dll` exports `TeGraphNetwork` and `TeNetwork` with `minimumPath`, `nearestNetworkPoint`,
`nearestNodePoint`, `getLineCosts`, `breakLineSet`, and the strategies `TeProxMatrixOpenNetworkStrategy`,
`TeProxMatrixOpenNetworkStrategy2` and `TeProxMatrixClosedNetworkStrategy`. `plugins/Gpm.dll` uses the first
and `plugins/CelulasConn.dll` the second. So the original open-network GPM computed the cost with a
`minimumPath` method of the network class. The algorithm cannot be read from the binaries without a
disassembly, which we did not do.

## TerraLib 4.2.2: the original open-network GPM used Dijkstra

Source: github.com/Universefei/Terralib-analysis (a copy of the TerraLib 4.2.2 sources; commit 2fb454a, 24 Mar 2014),
`src/terralib/kernel/TeNetwork.cpp` and `TeProxMatrixConstructionStrategy.cpp`.

* `TeGraphNetwork::insertLine` creates one graph edge per line, between its first and last points
  (nodes closer than 0.001 are the same node), with the cost of the line as weight.
* `TeGraphNetwork::minimumPath(n1, nodeSet, result)` calls `br_stl::Dijkstra` (`Gra_algo.h`) from node `n1`
  and returns the distance to each node of `nodeSet`.
* `TeProxMatrixOpenNetworkStrategy::Construct` finds, for each cell centroid, the nearest point of the network
  (`nearestNetworkPoint`), inserts it as a new node by breaking the line there with proportional costs
  (`breakLineSet`) if it is within `max_net_distance_`, and connects the geometries whose minimum path is
  within the maximum. Its comment: "Compute the minimum path among all these new nodes (entry points)".

## Is it the projection? No (10 Oct 2026)

The 8-line case of `../case_minimal` was transformed and run again in TerraME 2.0.1: translated by (-4.9e6, -9.7e6) m
(coordinates near zero), translated by (+3e6, +5e6) m, rotated by 37 degrees, and scaled by 0.1, 10, 100 and 1000
about the origin. The break (V 7.38 km above the cost of J plus the segment, scaled by the factor) appears in all of them,
and all node costs scale exactly with the factor (also at 1e-3 and 1e-5, tested for the scaling of the costs only).
The failure does not depend on the origin, orientation or magnitude of the coordinates.
The roads of the small example `data/roads.shp` of TerraME/gpm have a `.prj` of WGS84 degrees, but their coordinates
are in metres (about 763,000 E and 9,703,000 N, UTM-like): the file is mislabelled; the connectivity case is in
SIRGAS 2000 Polyconic (EPSG:5880). The small example gives no break in 40 random orders of its lines.
