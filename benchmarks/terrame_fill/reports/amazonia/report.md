# amazonia: DisSCube vs TerraME Fill

2229 cells, grid `amazonia_50km`, DisSCube 0.4.0.

| variable | cells | mean |err| | max |err| | bias | r | within tol | criterion | status |
|---|---|---|---|---|---|---|---|---|
| prodes_10 | 2174 | 6.74e-13 | 4.75e-11 | +1.57e-13 | 1.0000 | - | max <= 0.0001 | match |
| prodes_208 | 2174 | 1.12e-12 | 4.85e-11 | -1.39e-13 | 1.0000 | - | max <= 0.0001 | match |
| protected | 2229 | 1.75e-05 | 0.00433 | -1.75e-05 | 1.0000 | 100.0% (<= 0.01) | >= 99.0% within 0.01 | match |
| distroads | 2229 | 300 | 1.81e+04 | -300 | 0.9999 | 79.2% (<= 100) | >= 78.0% within 100 | match |
| distports | 2229 | 3.74e-05 | 0.000496 | -2.09e-06 | 1.0000 | 100.0% (<= 1) | >= 100.0% within 1 | match |

- **prodes_10**: coverage; identical to TerraME (same valid-pixel denominator)
- **prodes_208**: coverage, as above
- **protected**: area: intersection area / cell area with overlapping polygons counted once; TerraME's `area` is the same quantity
- **distroads**: distance (lines): TerraME measures to the nearest vertex, DisSCube to the segment; the gap grows where vertices are sparse (50 km cells)
- **distports**: distance (points): points are vertices, so both tools agree exactly
