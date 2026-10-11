# Node costs of the connectivity case

The golden stores the final cost of each cell, not the cost of the nodes inside the TerraME network.
These three files compare the node costs, which separates the network from the way a cell enters it.

1. DisSCube (any machine, after `make run DATASET=connectivity`):
   `python export_nodes_disscube.py --workspace ../data/connectivity --out nodes_disscube.csv`
   Checked: the node costs reproduce the DisSCube cell costs (vertex rule) to 1e-6 km, and the graph
   has 116,824 nodes.
2. TerraME (needs the `profsergiocosta/terrame-luccme` image):
   `export_nodes_terrame.lua` builds the same Network as `connectivity.lua` of luccme-goldens and writes
   `nodes_terrame.csv` (see the header of the file for the `docker run` line). Run with TerraME 2.0.1
   (sha256 `846fa303...`, the binary of terrame-docker 0.4.2) and its pinned gpm: `connectivity.lua` gives
   the golden to 5e-7 km, and the export takes about 8 s and writes 119,331 nodes.
3. `python compare_nodes.py nodes_disscube.csv nodes_terrame.csv --out nodes_compare.csv` matches nodes by
   position and prints the statistics of the difference.
4. `python check_shortest_path.py nodes_terrame.csv --workspace ../data/connectivity` counts the road segments whose
   two nodes differ in cost by more than the cost of the segment (impossible in an exact shortest-path solution).

Result (10 Oct 2026, `reports/connectivity/nodes_report.md`): the difference is already in the node costs.
