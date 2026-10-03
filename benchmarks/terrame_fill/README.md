# Suite: DisSCube vs TerraME *Fill*

Derives with DisSCube, **on the same grid**, the attributes of TerraME's `gis` *Fill* tutorial and
compares them cell by cell with the golden cellular spaces published in
[`LambdaGeo/luccme-goldens`](https://github.com/LambdaGeo/luccme-goldens) (`goldens/fill/`,
release `v1.0.0`, Zenodo DOI 10.5281/zenodo.23107748).

| Dataset | Grid | TerraME fills | DisSCube operators |
|---|---|---|---|
| `itaituba` | 31 × 20 cells, 5 km, EPSG:29191 | `average`, `coverage`, `distance`, `sum (area)` | `mean`, `percentage`, `distance`, `sum` (`area = true`) |
| `amazonia` | 2 229 cells, 50 km, EPSG:29191 | `coverage`, `distance`, `area` | `percentage`, `distance`, `area` |
| `majority` | 620 cells, 5 km, EPSG:29191 | `mode` (deforestation raster) | `majority` |
| `emas` | 5 514 cells, 500 m, EPSG:29192 | `presence`, `maximum`, `minimum` | `presence`, `max`, `min` |

## Run

```bash
pip install -r ../../requirements.txt
./run.sh all itaituba          # or: emas, amazonia, majority  (run = derive, compare = check, all = both)
```

`run` downloads TerraME's own `gis` package data from
[TerraME/terrame](https://github.com/TerraME/terrame) (pinned commit, SHA-256 verified) and derives the
variables. `compare` downloads the golden CSV, verifies its SHA-256 and exits with status 1 if a
comparison marked `expect = "match"` exceeds its criterion. Reports go to `reports/<dataset>/report.{md,json}`
(git-ignored). Offline: set `LUCCME_GOLDENS_DIR` to a local clone of `luccme-goldens`.

## Files

```
<dataset>.toml           DisSCube pipeline: grid, sources, derivations
<dataset>.compare.toml   golden URL + SHA-256, what is compared, criteria, expected differences
compare.py               metrics table + report.md/json; exit 1 on regression
run.sh                   run | compare | all
```

## Kinds of comparison (`<dataset>.compare.toml`)

- `expect = "match"`: has a criterion, `max_abs_error` and/or `min_share` at tolerance `tol`; the run fails if it is not met.
- `expect = "differs"`: reported only (no pass/fail). None at the moment.
- `kind = "categorical"`: class values (TerraME `mode`). The golden column is text: one class or, on a tie, every tied class separated by comma (`"7,87"`); a cell agrees when DisSCube's class is among them. Criterion: `min_share`.
- `[[unsupported]]`: TerraME operation with no DisSCube operator yet. None at the moment.

Cells are matched by centre coordinates (`cx`, `cy`), not by row number: TerraME numbers rows from the
south, DisSCube grids are north-up, and some references keep only a subset of the rectangle.
Coverage is compared as a fraction (0–1), as stored in the goldens.

Thresholds were set against `luccme-goldens` v1.0.0 and DisSCube `main` (commit `cef6ee2`) plus a small margin. `sum` with `area = true` (Itaituba `population`) is not in the PyPI 0.4.0 release yet.

## Data

The input layers are © INPE and TerraLAB/UFOP (GNU LGPL), downloaded at run time and never stored in this repository.
