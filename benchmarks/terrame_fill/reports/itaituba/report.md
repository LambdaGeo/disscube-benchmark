# itaituba: DisSCube vs TerraME Fill

620 cells, grid `itaituba_5km`, DisSCube 0.4.0.

| variable | cells | mean |err| | max |err| | bias | r | within tol | criterion | status |
|---|---|---|---|---|---|---|---|---|
| elevation | 620 | 0.889 | 10.1 | -0.0746 | 0.9995 | - | max <= 11 | match |
| defor_7 | 620 | 0.00054 | 0.00638 | -3.4e-05 | 1.0000 | - | max <= 0.01 | match |
| defor_87 | 620 | 0.000541 | 0.00638 | +1.43e-05 | 1.0000 | - | max <= 0.01 | match |
| defor_167 | 620 | 6.49e-05 | 0.00395 | +1.97e-05 | 1.0000 | - | max <= 0.01 | match |
| defor_255 | 620 | 5.15e-08 | 2.16e-05 | -1.83e-08 | 1.0000 | - | max <= 0.01 | match |
| distroad | 620 | 24 | 1.88e+03 | -24 | 0.9999 | 94.5% (<= 100) | >= 94.0% within 100 | match |
| distlocal | 620 | 1.24e-06 | 4.96e-06 | +3.28e-08 | 1.0000 | 100.0% (<= 1) | >= 100.0% within 1 | match |
| population | 620 | 9.08e-09 | 3.81e-07 | -6.13e-11 | 1.0000 | - | max <= 1e-05 | match |

- **elevation**: TerraME average vs DisSCube mean (area-weighted resampling of a 923 m raster)
- **defor_7**: coverage; same valid-pixel denominator in both
- **defor_87**: coverage
- **defor_167**: coverage
- **defor_255**: coverage
- **distroad**: distance (lines): TerraME measures to the nearest vertex, DisSCube to the segment, so it is never larger
- **distlocal**: distance (points): points are vertices, so both tools agree exactly
- **population**: sum with area = true: census population shared by intersected area (total conserved)
