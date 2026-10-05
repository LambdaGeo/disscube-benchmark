# emas: DisSCube vs TerraME Fill

5514 cells, grid `emas_500m`, DisSCube 0.4.0.

| variable | cells | mean |err| | max |err| | bias | r | within tol | criterion | status |
|---|---|---|---|---|---|---|---|---|
| firebreak | 5514 | 0.016 | 1 | -0.0149 | 0.9371 | 98.4% (<= 0) | >= 98.0% within 0 | match |
| river | 5514 | 0.00272 | 1 | -0.00272 | 0.9884 | 99.7% (<= 0) | >= 98.0% within 0 | match |
| maxcover | 5514 | 0.0381 | 5 | +0.0381 | 0.9787 | 98.7% (<= 0) | >= 98.5% within 0 | match |
| mincover | 5514 | 0.0232 | 5 | -0.0232 | 0.9863 | 99.0% (<= 0) | >= 98.5% within 0 | match |

- **firebreak**: presence: DisSCube rasterizes lines through cell centres, TerraME marks every cell a line touches
- **river**: presence, as above
- **maxcover**: max: pixels straddling a cell border count for both cells in DisSCube; TerraME assigns each pixel to the cell holding its centre
- **mincover**: min, as above
