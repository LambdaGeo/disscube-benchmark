# Node costs: DisSCube vs TerraME (connectivity case)

Run of 10 Oct 2026. DisSCube 0.5.0 (`export_nodes_disscube.py`, pipeline `connectivity.toml`); TerraME 2.0.1
(sha256 `846fa303a6e9dbe1869456e7a525186618595789eec276164b8afbb0ca7e33ed`, Ubuntu 18.04) with the gpm of
terrame-docker 0.4.2 (`export_nodes_terrame.lua`). With the same binary and gpm, `connectivity.lua` gives the
golden `connectivity_terrame.csv` to 5e-7 km (14,255 cells).

| | nodes |
|---|---:|
| DisSCube graph | 116,824 |
| TerraME network | 119,331 |
| Matched by position (0.5 m) | 116,824 (all of DisSCube) |
| Only in TerraME | 2,507 |

Difference in node cost, DisSCube minus TerraME (km), over the 116,824 matched nodes:

| mean | median | 1% | 5% | 95% | 99% | min | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| -10.02 | -2.90 | -81.06 | -39.71 | 1.36 | 1.87 | -274.44 | 1.87 |

- Equal within 0.01 km: 12.8% of the nodes. DisSCube lower by more than 1 km: 57.9%. More than 25 km apart (either sign): 13,376 nodes.
- DisSCube is higher than TerraME in 24,318 nodes, never by more than 1.87 km.

Cell costs rebuilt from a set of nodes by the vertex rule (nearest node plus 0.002 km per metre off the
network), against the golden:

| nodes used | mean abs error (km) | max (km) | within 0.01 km | within 1 km |
|---|---:|---:|---:|---:|
| TerraME | 1.14 | 253.4 | 52.3% | 89.3% |
| DisSCube | 27.06 | 369.9 | 5.1% | 16.9% |

Reading: the vertex rule explains the golden when it is applied to the TerraME node costs, so the offset
between the two cost surfaces is already in the costs of the nodes (the cost along the network), not in the
way a cell enters it.

## Shortest-path condition (`check_shortest_path.py`)

In an exact shortest-path solution, two nodes joined by a road segment differ in cost by at most the cost of
the segment. Over the 120,292 segments of the road file:

| node costs | segments that break the condition | size of the breaks (km) | first or last segment of its line |
|---|---:|---|---:|
| DisSCube | 0 | - | - |
| TerraME | 827 or 828 (0.69%), see below | median 5.91, 95th percentile 41.0, maximum 247.6 | 100% of the breaks (26.1% of all segments) |

The count is not the same in every run of TerraME: with the same binary, the same gpm and the same inputs, six
runs of `export_nodes_terrame.lua` gave 827 breaks four times and 828 twice (the table shows the first export, 828). The
node costs of the runs differ in one node (up to 27 km) and the node count is 119,331 in all of them; we have not looked
for the cause of the difference between runs. The node costs of TerraME are therefore not the shortest-path distances of its own road graph, and the breaks sit
where two lines meet. This agrees with a network that is built incrementally and revised along stored
`next`/`previous` chains (`reviewExistingNode` and `reviewNextNodes` in `gpm/lua/Network.lua`) instead of
solved as a whole. The code was read, but no single case has been traced to a line of it.
