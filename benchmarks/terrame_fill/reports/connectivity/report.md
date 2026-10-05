# connectivity: DisSCube vs TerraME Fill

14255 cells, grid `br_25km`, DisSCube 0.4.0.

| variable | cells | mean |err| | max |err| | bias | r | within tol | criterion | status |
|---|---|---|---|---|---|---|---|---|
| cost | 14255 | 27.1 | 370 | -25.3 | 0.9960 | 51.9% (<= 25) | max <= 85; >= 80.0% within 25 | differs |

- **cost**: GTC to ports: DisSCube (optimal Dijkstra lower bound) vs TerraME GPM (heuristic propagation)
